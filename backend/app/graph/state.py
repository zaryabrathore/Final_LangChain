from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """LangGraph State holding conversation, sub-agent routes, and tool execution data."""
    user_query: str
    messages: List[Dict[str, str]]
    next_step: str
    active_agent: str
    rag_context: List[Dict[str, Any]]
    github_result: Optional[Dict[str, Any]]
    google_result: Optional[Dict[str, Any]]
    agent_response: str
    execution_logs: List[Dict[str, Any]]
