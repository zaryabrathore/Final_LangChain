import json
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, Any
from app.mcp.google_mcp_client import google_mcp_client
from app.config import settings

logger = logging.getLogger(__name__)

def _heuristic_dispatch(query: str, query_lower: str) -> tuple[str, Dict[str, Any]]:
    """Fallback heuristic parser when Gemini structured extraction is unavailable."""
    emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
    
    # 1. Schedule & Notify (Meeting + Email)
    if ("schedule" in query_lower or "create" in query_lower or "book" in query_lower) and ("email" in query_lower or "notify" in query_lower or "invite" in query_lower or "send" in query_lower):
        recipient = emails[0] if emails else "colleague@example.com"
        # Attempt to extract meeting title from quotes if present
        title_match = re.search(r'["\']([^"\']+)["\']', query)
        summary = title_match.group(1) if title_match else "Scheduled Sync & Review"
        default_time = (datetime.now() + timedelta(days=1)).replace(hour=14, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:00Z")
        return "schedule_meeting_and_notify", {
            "recipient_email": recipient,
            "meeting_summary": summary,
            "meeting_time": default_time,
            "duration_minutes": 30,
            "email_note": "Meeting scheduled via Google Workspace MCP Agent."
        }

    # 2. Create Calendar Meeting
    elif any(act in query_lower for act in ["create", "schedule", "book", "add", "set up", "new"]) and any(noun in query_lower for noun in ["meeting", "event", "calendar", "call", "appointment", "sync"]):
        title_match = re.search(r'["\']([^"\']+)["\']', query)
        summary = title_match.group(1) if title_match else "Team Sync Session"
        default_time = (datetime.now() + timedelta(days=1)).replace(hour=10, minute=0, second=0).strftime("%Y-%m-%dT%H:%M:00Z")
        return "calendar_create_meeting", {
            "summary": summary,
            "start_time": default_time,
            "duration_minutes": 45,
            "attendees": emails if emails else [settings.google_user_email],
            "description": f"Created via Google Workspace MCP Agent for request: {query}"
        }

    # 3. Draft Email
    elif "draft" in query_lower or "write email" in query_lower:
        to_email = emails[0] if emails else "client@example.com"
        return "email_write_draft", {
            "to_email": to_email,
            "subject": "Follow-up & Discussion Notes",
            "body": f"Hello,\n\nI am writing to follow up regarding: {query}\n\nBest regards,"
        }

    # 4. Send Email Now
    elif "send email" in query_lower or "send mail" in query_lower or ("send" in query_lower and "email" in query_lower):
        to_email = emails[0] if emails else "partner@example.com"
        return "email_send_now", {
            "to_email": to_email,
            "subject": "Important Workspace Update",
            "body": f"Hi,\n\n{query}\n\nSent via Google Workspace MCP Sub-Agent."
        }

    # 5. Default / Read Meetings
    else:
        return "calendar_read_meetings", {"days_ahead": 7}


def run_google_workspace_sub_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Sub-Agent 03: Google Calendar & Gmail MCP Sub-Agent."""
    query = state.get("user_query", "")
    query_lower = query.lower()
    logger.info(f"Google Workspace Sub-Agent processing query: {query}")

    tool_name = None
    args = {}

    # Try Gemini LLM to extract tool and arguments dynamically
    if settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",
                google_api_key=settings.gemini_api_key,
                temperature=0.1
            )

            tools_schema = json.dumps(google_mcp_client.get_mcp_tool_definitions(), indent=2)
            current_dt = datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ")

            system_prompt = (
                f"You are the Tool Dispatcher for Google Workspace MCP (Calendar & Gmail).\n"
                f"Current Date/Time: {current_dt}\n"
                f"Available MCP Tools Schema:\n{tools_schema}\n\n"
                f"Your task: Given the user query, determine the single best MCP tool to call and construct its arguments dictionary.\n"
                f"Respond ONLY with valid JSON in this exact structure without markdown backticks:\n"
                f'{{"tool_name": "<name>", "arguments": {{...}}}}\n\n'
                f"Rules:\n"
                f"- For calendar meetings, if start_time is relative (e.g. tomorrow at 3pm), compute an ISO 8601 string relative to {current_dt}.\n"
                f"- If user asks to list/read calendar events, use 'calendar_read_meetings'.\n"
                f"- If user asks to schedule a meeting AND send email/invite, use 'schedule_meeting_and_notify'."
            )

            res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)])
            cleaned_text = res.content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned_text)

            if "tool_name" in parsed and "arguments" in parsed:
                tool_name = parsed["tool_name"]
                args = parsed["arguments"]
                logger.info(f"Gemini dynamic tool resolution: {tool_name} with args {args}")
        except Exception as e:
            logger.warning(f"Gemini LLM tool dispatch extraction failed ({e}), falling back to heuristic.")

    # Fallback to heuristic dispatch if Gemini was not used or failed
    if not tool_name:
        tool_name, args = _heuristic_dispatch(query, query_lower)

    # Execute selected MCP tool
    mcp_res = google_mcp_client.execute_mcp_tool(tool_name, args)

    # Generate final user response
    if settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash",
                google_api_key=settings.gemini_api_key,
                temperature=0.2
            )
            prompt = (
                f"You are the Google Workspace MCP Sub-Agent (Calendar & Gmail). Answer the user request using the raw MCP tool output below.\n\n"
                f"User Request: {query}\n"
                f"Executed MCP Tool: {tool_name}\n"
                f"MCP Tool Arguments: {json.dumps(args)}\n"
                f"MCP Output Data: {json.dumps(mcp_res)}\n\n"
                f"Provide a clear, human-friendly summary of the actions taken."
            )
            res = llm.invoke([HumanMessage(content=prompt)])
            response_text = res.content
        except Exception as e:
            logger.warning(f"Gemini response formatting error: {e}")
            response_text = f"**Google Workspace MCP Sub-Agent Response (`{tool_name}`)**:\n\n{mcp_res.get('message', str(mcp_res))}"
    else:
        if tool_name == "calendar_read_meetings":
            meetings = mcp_res.get("meetings", [])
            if not meetings:
                response_text = "📅 **No upcoming Google Calendar meetings found.**"
            else:
                m_lines = [f"- 📅 **{m.get('summary', 'Meeting')}** ({m.get('start_time', 'N/A')}) -> [Google Meet Link]({m.get('meet_link', '#')})" for m in meetings]
                response_text = f"📅 **Google Calendar Meetings ({mcp_res.get('source', 'Workspace')}):**\n\n" + "\n".join(m_lines)
        elif tool_name == "schedule_meeting_and_notify":
            m = mcp_res.get("calendar_event", {})
            em = mcp_res.get("email_sent", {})
            response_text = (
                f"✅ **Google Workspace Action Completed:**\n\n"
                f"- **Google Meeting Scheduled:** '{m.get('summary')}' at `{m.get('start_time')}`\n"
                f"- **Google Meet Link:** {m.get('meet_link')}\n"
                f"- **Email Status:** {mcp_res.get('message', 'Invitation processed.')}"
            )
        else:
            response_text = f"✅ **Google Workspace MCP Result (`{tool_name}`):**\n\n{mcp_res.get('message', str(mcp_res))}"

    logs = state.get("execution_logs", [])
    logs.append({
        "node": "google_workspace_sub_agent",
        "status": "completed",
        "mcp_tool": tool_name,
        "details": f"Executed Google Workspace MCP tool '{tool_name}' successfully."
    })

    return {
        "google_result": mcp_res,
        "agent_response": response_text,
        "active_agent": "google_workspace_sub_agent",
        "execution_logs": logs
    }

