import logging
import re
from typing import Dict, Any
from app.mcp.google_mcp_client import google_mcp_client
from app.config import settings

logger = logging.getLogger(__name__)

def run_google_workspace_sub_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Sub-Agent 03: Google Calendar & Gmail MCP Sub-Agent."""
    query = state.get("user_query", "")
    query_lower = query.lower()
    logger.info(f"Google Workspace Sub-Agent processing query: {query}")

    # Tool Intent Dispatcher
    if "schedule" in query_lower and ("email" in query_lower or "notify" in query_lower or "invite" in query_lower or "send" in query_lower):
        tool_name = "schedule_meeting_and_notify"
        # Extract email if present
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
        recipient = emails[0] if emails else "colleague@example.com"
        args = {
            "recipient_email": recipient,
            "meeting_summary": "Sync & Review Meeting",
            "meeting_time": "2026-10-04T15:00:00Z",
            "duration_minutes": 45,
            "email_note": "Please review the attached agenda prior to the call."
        }
    elif "create" in query_lower and ("meeting" in query_lower or "event" in query_lower or "calendar" in query_lower):
        tool_name = "calendar_create_meeting"
        args = {
            "summary": "Team Strategy Session",
            "start_time": "2026-10-03T16:00:00Z",
            "duration_minutes": 60,
            "attendees": [settings.google_user_email],
            "description": "Created via Google Workspace MCP Agent."
        }
    elif "draft" in query_lower or "write email" in query_lower:
        tool_name = "email_write_draft"
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
        to_email = emails[0] if emails else "client@example.com"
        args = {
            "to_email": to_email,
            "subject": "Discussion Follow-up & Project Update",
            "body": f"Hello,\n\nI am writing to follow up on our previous conversation regarding the LangGraph agent deployment.\n\nBest regards,"
        }
    elif "send email" in query_lower or "send an email" in query_lower or "mail" in query_lower and "send" in query_lower:
        tool_name = "email_send_now"
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', query)
        to_email = emails[0] if emails else "partner@example.com"
        args = {
            "to_email": to_email,
            "subject": "Urgent: Project Approval Confirmation",
            "body": "Hi,\n\nThis email confirms that all LangGraph MCP sub-agents are operational and ready for production."
        }
    else:
        # Default: read calendar meetings
        tool_name = "calendar_read_meetings"
        args = {"days_ahead": 7}

    mcp_res = google_mcp_client.execute_mcp_tool(tool_name, args)

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
                f"MCP Output Data: {mcp_res}\n\n"
                f"Provide a clear, human-friendly summary of the actions taken (e.g., meeting created, email draft written, email sent, or meetings read)."
            )
            res = llm.invoke([HumanMessage(content=prompt)])
            response_text = res.content
        except Exception as e:
            logger.warning(f"Gemini LLM Google Workspace MCP invocation error: {e}")
            response_text = f"**Google Workspace MCP Sub-Agent Response (`{tool_name}`)**:\n\n{mcp_res.get('message', str(mcp_res))}"
    else:
        if tool_name == "calendar_read_meetings":
            meetings = mcp_res.get("meetings", [])
            m_lines = [f"- 📅 **{m['summary']}** ({m['start_time']}) -> [Google Meet]({m.get('meet_link', '#')})" for m in meetings]
            response_text = "📅 **Upcoming Google Calendar Meetings:**\n\n" + "\n".join(m_lines)
        elif tool_name == "schedule_meeting_and_notify":
            m = mcp_res.get("calendar_event", {})
            em = mcp_res.get("email_sent", {})
            response_text = (
                f"✅ **Google Workspace MCP Action Completed:**\n\n"
                f"- **Google Meeting Scheduled:** '{m.get('summary')}' at `{m.get('start_time')}`\n"
                f"- **Google Meet Link:** {m.get('meet_link')}\n"
                f"- **Email Sent to Recipient:** Sent to `{em.get('to')}` with subject '{em.get('subject')}'"
            )
        else:
            response_text = f"✅ **Google Workspace MCP Result ({tool_name}):**\n\n{mcp_res.get('message', str(mcp_res))}"

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
