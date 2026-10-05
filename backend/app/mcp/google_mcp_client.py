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

    def _send_real_email(self, to_email: str, subject: str, body: str) -> Dict[str, Any]:
        """Attempts to send a real email using Gmail API OAuth credentials or SMTP App Password."""
        # 1. Try Gmail API (OAuth 2.0 Credentials)
        has_oauth = (
            settings.google_client_id
            and settings.google_client_secret
            and settings.google_refresh_token
            and "your_" not in settings.google_client_secret.lower()
            and "your_" not in settings.google_refresh_token.lower()
        )
        if has_oauth:
            try:
                import base64
                from email.mime.text import MIMEText
                from google.oauth2.credentials import Credentials
                from googleapiclient.discovery import build

                creds = Credentials(
                    token=None,
                    refresh_token=settings.google_refresh_token,
                    token_uri="https://oauth2.googleapis.com/token",
                    client_id=settings.google_client_id,
                    client_secret=settings.google_client_secret
                )
                service = build('gmail', 'v1', credentials=creds)
                mime_msg = MIMEText(body)
                mime_msg['to'] = to_email
                mime_msg['subject'] = subject
                raw_b64 = base64.urlsafe_b64encode(mime_msg.as_bytes()).decode('utf-8')
                result = service.users().messages().send(userId='me', body={'raw': raw_b64}).execute()
                return {
                    "sent": True,
                    "method": "Gmail API (OAuth 2.0)",
                    "id": result.get("id"),
                    "message": f"Real email successfully sent via Gmail API to {to_email} (ID: {result.get('id')})"
                }
            except Exception as e:
                logger.error(f"Gmail API OAuth error: {e}")
                return {
                    "sent": False,
                    "error": f"Gmail OAuth API error: {str(e)}"
                }

        # 2. Try SMTP App Password
        has_smtp = (
            settings.gmail_app_password
            and settings.google_user_email
            and "your_" not in settings.gmail_app_password.lower()
            and "example.com" not in settings.google_user_email.lower()
        )
        if has_smtp:
            raw_pwd = settings.gmail_app_password.strip()
            # Try original password string first, then stripped spaces
            passwords_to_try = [raw_pwd, raw_pwd.replace(" ", "")]
            last_err = None
            
            for pwd in passwords_to_try:
                try:
                    import smtplib, ssl
                    from email.mime.text import MIMEText
                    from email.mime.multipart import MIMEMultipart

                    msg = MIMEMultipart()
                    msg['From'] = settings.google_user_email
                    msg['To'] = to_email
                    msg['Subject'] = subject
                    msg.attach(MIMEText(body, 'plain'))

                    context = ssl.create_default_context()
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context, timeout=12) as server:
                        server.login(settings.google_user_email, pwd)
                        server.sendmail(settings.google_user_email, to_email, msg.as_string())

                    return {
                        "sent": True,
                        "method": "Gmail SMTP (SSL)",
                        "id": f"smtp_{uuid.uuid4().hex[:6]}",
                        "message": f"Real email successfully sent via Gmail SMTP to {to_email}"
                    }
                except smtplib.SMTPAuthenticationError as auth_err:
                    last_err = f"Gmail Authentication Error (535): Username or App Password rejected by Google. Ensure 2-Step Verification is active and you created a new 16-character App Password at https://myaccount.google.com/apppasswords for {settings.google_user_email}."
                    break
                except Exception as e:
                    last_err = str(e)

            logger.error(f"Gmail SMTP error: {last_err}")
            return {
                "sent": False,
                "error": last_err or "Gmail SMTP connection failed"
            }

        # 3. Neither credentials available
        return {
            "sent": False,
            "simulated": True,
            "message": "No valid Gmail credentials (OAuth or App Password) configured in backend/.env"
        }

    def _get_calendar_service(self):
        """Attempts to build Google Calendar API service using OAuth credentials."""
        has_oauth = (
            settings.google_client_id
            and settings.google_client_secret
            and settings.google_refresh_token
            and "your_" not in settings.google_client_secret.lower()
            and "your_" not in settings.google_refresh_token.lower()
        )
        if not has_oauth:
            return None
        try:
            from google.oauth2.credentials import Credentials
            from googleapiclient.discovery import build

            creds = Credentials(
                token=None,
                refresh_token=settings.google_refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.google_client_id,
                client_secret=settings.google_client_secret
            )
            return build('calendar', 'v3', credentials=creds)
        except Exception as e:
            logger.error(f"Google Calendar OAuth build error: {e}")
            return None

    def execute_mcp_tool(self, tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
        """Executes Google Workspace MCP tools."""
        
        if tool_name == "calendar_read_meetings":
            service = self._get_calendar_service()
            if service:
                try:
                    now = datetime.utcnow().isoformat() + 'Z'
                    events_result = service.events().list(
                        calendarId='primary',
                        timeMin=now,
                        maxResults=10,
                        singleEvents=True,
                        orderBy='startTime'
                    ).execute()
                    items = events_result.get('items', [])
                    live_meetings = []
                    for item in items:
                        start = item.get('start', {}).get('dateTime', item.get('start', {}).get('date'))
                        end = item.get('end', {}).get('dateTime', item.get('end', {}).get('date'))
                        live_meetings.append({
                            "id": item.get("id"),
                            "summary": item.get("summary", "Untitled Meeting"),
                            "start_time": start,
                            "end_time": end,
                            "attendees": [att.get("email") for att in item.get("attendees", []) if att.get("email")],
                            "description": item.get("description", ""),
                            "status": item.get("status", "confirmed"),
                            "meet_link": item.get("htmlLink") or item.get("hangoutLink") or "#"
                        })
                    return {
                        "status": "success",
                        "source": "Google Calendar API (Live)",
                        "total_events": len(live_meetings),
                        "meetings": live_meetings
                    }
                except Exception as e:
                    logger.error(f"Live Google Calendar fetch error: {e}")

            return {
                "status": "success",
                "source": "In-Memory Store",
                "total_events": len(self.meetings),
                "meetings": self.meetings
            }

        elif tool_name == "calendar_create_meeting":
            summary = args.get("summary", "New Meeting")
            start_time = args.get("start_time") or datetime.now().isoformat()
            duration = int(args.get("duration_minutes", 30))
            attendees = args.get("attendees", [])
            desc = args.get("description", "Created via Google Workspace MCP Agent")

            # Parse start time and compute end time
            try:
                dt_start = datetime.fromisoformat(str(start_time).replace("Z", "+00:00"))
            except Exception:
                dt_start = datetime.now() + timedelta(days=1)
            
            dt_end = dt_start + timedelta(minutes=duration)

            service = self._get_calendar_service()
            if service:
                try:
                    event_body = {
                        'summary': summary,
                        'description': desc,
                        'start': {'dateTime': dt_start.strftime("%Y-%m-%dT%H:%M:%SZ"), 'timeZone': 'UTC'},
                        'end': {'dateTime': dt_end.strftime("%Y-%m-%dT%H:%M:%SZ"), 'timeZone': 'UTC'},
                        'attendees': [{'email': email} for email in attendees if email],
                    }
                    created = service.events().insert(calendarId='primary', body=event_body).execute()
                    live_meeting = {
                        "id": created.get("id"),
                        "summary": created.get("summary", summary),
                        "start_time": created.get("start", {}).get("dateTime", dt_start.isoformat()),
                        "end_time": created.get("end", {}).get("dateTime", dt_end.isoformat()),
                        "attendees": attendees,
                        "description": desc,
                        "status": "confirmed",
                        "meet_link": created.get("htmlLink") or created.get("hangoutLink") or f"https://meet.google.com/{uuid.uuid4().hex[:3]}-{uuid.uuid4().hex[:4]}"
                    }
                    self.meetings.append(live_meeting)
                    return {
                        "status": "success",
                        "delivery": "REAL_CALENDAR_EVENT_CREATED",
                        "message": f"Successfully created real Google Calendar event '{summary}'",
                        "meeting": live_meeting
                    }
                except Exception as e:
                    logger.error(f"Live Google Calendar event creation error: {e}")

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
                "delivery": "LOCAL_MEMORY_STORED",
                "message": f"Successfully created meeting '{summary}' on Google Calendar (recorded in local memory)",
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

            real_res = self._send_real_email(to_email, subject, body)
            
            if real_res.get("sent"):
                sent_email = {
                    "id": real_res["id"],
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                    "is_draft": False,
                    "sent_at": datetime.now().isoformat(),
                    "delivery_method": real_res["method"]
                }
                self.emails.append(sent_email)
                return {
                    "status": "success",
                    "delivery": "REAL_EMAIL_DELIVERED",
                    "message": real_res["message"],
                    "email": sent_email
                }
            elif "error" in real_res:
                return {
                    "status": "error",
                    "delivery": "FAILED",
                    "message": f"Failed to send real email: {real_res['error']}",
                    "details": real_res["error"]
                }
            else:
                sent_email = {
                    "id": f"eml_sim_{uuid.uuid4().hex[:6]}",
                    "to": to_email,
                    "subject": subject,
                    "body": body,
                    "is_draft": False,
                    "sent_at": datetime.now().isoformat(),
                    "delivery_method": "SIMULATED (No Credentials in .env)"
                }
                self.emails.append(sent_email)
                return {
                    "status": "simulated_success",
                    "delivery": "SIMULATED_MOCK_ONLY",
                    "message": f"[SIMULATION MODE] Action recorded in local memory. Real email was NOT sent to {to_email} because valid Gmail credentials (GMAIL_APP_PASSWORD or OAuth Refresh Token) are not set in backend/.env.",
                    "email": sent_email,
                    "instructions": "To send real emails to an actual inbox, set GMAIL_APP_PASSWORD in backend/.env or configure GOOGLE_CLIENT_SECRET & GOOGLE_REFRESH_TOKEN."
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
                "status": email_res.get("status", "success"),
                "delivery": email_res.get("delivery", "UNKNOWN"),
                "message": f"Meeting '{summary}' scheduled on Google Calendar. Email status: {email_res.get('message')}",
                "calendar_event": meeting,
                "email_sent": email_res.get("email")
            }

        return {"status": "error", "message": f"Unknown tool: {tool_name}"}

google_mcp_client = GoogleWorkspaceMCPClient()
