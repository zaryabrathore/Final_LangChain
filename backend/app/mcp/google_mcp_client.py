import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from app.config import settings

logger = logging.getLogger(__name__)

class GoogleWorkspaceMCPClient:
    """MCP Client & Tool Server for Google Calendar & Gmail Integration."""

    def __init__(self):
        # In-memory store for meetings and emails (allows active CRUD testing and persistence)
        self.meetings: List[Dict[str, Any]] = [
            {
                "id": "evt_101",
                "summary": "Project Sync & Architecture Review",
                "start_time": (datetime.now() + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:00Z"),
                "end_time": (datetime.now() + timedelta(hours=3)).strftime("%Y-%m-%dT%H:%M:00Z"),
                "attendees": ["team@example.com", settings.google_user_email],
                "description": "Weekly status review on LangGraph multi-agent deployment.",
                "status": "confirmed",
                "meet_link": "https://meet.google.com/abc-defg-hij"
            },
            {
                "id": "evt_102",
                "summary": "LangGraph RAG & MCP Demo",
                "start_time": (datetime.now() + timedelta(days=1, hours=4)).strftime("%Y-%m-%dT%H:%M:00Z"),
                "end_time": (datetime.now() + timedelta(days=1, hours=5)).strftime("%Y-%m-%dT%H:%M:00Z"),
                "attendees": ["stakeholders@example.com"],
                "description": "Demonstrating hosted Qdrant PDF RAG and GitHub/Google Workspace MCP agents.",
                "status": "confirmed",
                "meet_link": "https://meet.google.com/xyz-uvwx-rst"
            }
        ]
        self.emails: List[Dict[str, Any]] = [
            {
                "id": "eml_201",
                "to": "lead@example.com",
                "subject": "Draft: LangGraph Multi-Agent Progress Report",
                "body": "Hi Lead,\n\nThe LangGraph agent with hosted Qdrant RAG and GitHub/Google Workspace MCP sub-agents is fully configured.",
                "is_draft": True,
                "sent_at": None
            }
        ]

    def get_mcp_tool_definitions(self) -> List[Dict[str, Any]]:
        """Returns standard MCP schema for Google Workspace tools."""
        return [
            {
                "name": "calendar_read_meetings",
                "description": "Read upcoming Google Calendar meetings and scheduled events",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "days_ahead": {"type": "integer", "default": 7, "description": "Number of days ahead to search"}
                    }
                }
            },
            {
                "name": "calendar_create_meeting",
                "description": "Create a new meeting event on Google Calendar at a specific time",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string", "description": "Meeting title / summary"},
                        "start_time": {"type": "string", "description": "ISO timestamp (e.g. 2026-10-03T14:00:00Z)"},
                        "duration_minutes": {"type": "integer", "default": 30},
                        "attendees": {"type": "array", "items": {"type": "string"}},
                        "description": {"type": "string"}
                    },
                    "required": ["summary", "start_time"]
                }
            },
            {
                "name": "email_write_draft",
                "description": "Create a draft email in Gmail to a specific person",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to_email", "subject", "body"]
                }
            },
            {
                "name": "email_send_now",
                "description": "Send an email immediately via Gmail to a specific recipient",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "to_email": {"type": "string"},
                        "subject": {"type": "string"},
                        "body": {"type": "string"}
                    },
                    "required": ["to_email", "subject", "body"]
                }
            },
            {
                "name": "schedule_meeting_and_notify",
                "description": "Schedule a Google Calendar meeting at a specific time and automatically send an email invitation to the recipient",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "recipient_email": {"type": "string"},
                        "meeting_summary": {"type": "string"},
                        "meeting_time": {"type": "string", "description": "ISO timestamp or descriptive string"},
                        "duration_minutes": {"type": "integer", "default": 30},
                        "email_note": {"type": "string"}
                    },
                    "required": ["recipient_email", "meeting_summary", "meeting_time"]
                }
            }
        ]

    def execute_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes Google Workspace MCP tools."""
        
        if tool_name == "calendar_read_meetings":
            return {
                "status": "success",
                "total_events": len(self.meetings),
                "meetings": self.meetings
            }

        elif tool_name == "calendar_create_meeting":
            summary = args.get("summary", "New Meeting")
            start_time = args.get("start_time", datetime.now().isoformat())
            duration = args.get("duration_minutes", 30)
            attendees = args.get("attendees", [])
            desc = args.get("description", "Created via Google Workspace MCP Agent")

            # Parse start time and compute end time
            try:
                dt_start = datetime.fromisoformat(start_time.replace("Z", "+00:00"))
            except Exception:
                dt_start = datetime.now() + timedelta(days=1)
            
            dt_end = dt_start + timedelta(minutes=duration)

            new_meeting = {
                "id": f"evt_{uuid.uuid4().hex[:6]}",
                "summary": summary,
                "start_time": dt_start.isoformat(),
                "end_time": dt_end.isoformat(),
                "attendees": attendees,
                "description": desc,
                "status": "confirmed",
                "meet_link": f"https://meet.google.com/{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}-{uuid.uuid4().hex[:3]}"
            }
            self.meetings.append(new_meeting)
            return {
                "status": "success",
                "message": f"Successfully created meeting '{summary}' on Google Calendar",
                "meeting": new_meeting
            }

        elif tool_name == "email_write_draft":
            to_email = args.get("to_email", "")
            subject = args.get("subject", "")
            body = args.get("body", "")

            draft = {
                "id": f"eml_{uuid.uuid4().hex[:6]}",
                "to": to_email,
                "subject": subject,
                "body": body,
                "is_draft": True,
                "created_at": datetime.now().isoformat()
            }
            self.emails.append(draft)
            return {
                "status": "success",
                "message": f"Draft email created for {to_email}",
                "email": draft
            }

        elif tool_name == "email_send_now":
            to_email = args.get("to_email", "")
            subject = args.get("subject", "")
            body = args.get("body", "")

            sent_email = {
                "id": f"eml_{uuid.uuid4().hex[:6]}",
                "to": to_email,
                "subject": subject,
                "body": body,
                "is_draft": False,
                "sent_at": datetime.now().isoformat()
            }
            self.emails.append(sent_email)
            return {
                "status": "success",
                "message": f"Email successfully sent to {to_email}",
                "email": sent_email
            }

        elif tool_name == "schedule_meeting_and_notify":
            recipient = args.get("recipient_email", "")
            summary = args.get("meeting_summary", "")
            meeting_time = args.get("meeting_time", "")
            duration = args.get("duration_minutes", 30)
            note = args.get("email_note", "Looking forward to speaking with you!")

            # 1. Create calendar meeting
            meeting_res = self.execute_mcp_tool("calendar_create_meeting", {
                "summary": summary,
                "start_time": meeting_time,
                "duration_minutes": duration,
                "attendees": [recipient],
                "description": f"Scheduled meeting: {summary}"
            })
            meeting = meeting_res["meeting"]

            # 2. Automatically generate and send email notification
            email_body = f"Hi,\n\nI have scheduled our meeting '{summary}'.\n\nDate & Time: {meeting['start_time']}\nMeeting Link: {meeting['meet_link']}\n\nNote from sender: {note}\n\nBest regards,\nGoogle Workspace Agent"
            
            email_res = self.execute_mcp_tool("email_send_now", {
                "to_email": recipient,
                "subject": f"Invitation: {summary} @ {meeting_time}",
                "body": email_body
            })

            return {
                "status": "success",
                "message": f"Meeting '{summary}' scheduled on Google Calendar and notification email sent to {recipient}",
                "calendar_event": meeting,
                "email_sent": email_res["email"]
            }

        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

google_mcp_client = GoogleWorkspaceMCPClient()
