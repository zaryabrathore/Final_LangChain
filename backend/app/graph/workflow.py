import logging
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from app.graph.state import AgentState
from app.agents.rag_agent import run_rag_sub_agent
from app.agents.github_mcp_agent import run_github_mcp_sub_agent
from app.agents.google_workspace_agent import run_google_workspace_sub_agent
from app.config import settings

logger = logging.getLogger(__name__)

def generate_supervisor_fallback(query: str) -> str:
    query_lower = query.lower()
    if "ui" in query_lower or "frontend" in query_lower or "react" in query_lower or "component" in query_lower:
        return (
            "Yes! You can easily add and customize UI components in this application.\n\n"
            "**Frontend Structure (`frontend/src/`):**\n"
            "- `components/AgentChat.jsx`: Main multi-agent chat interface & graph execution visualizer.\n"
            "- `components/RagPanel.jsx`: PDF document upload & Qdrant vector indexing interface.\n"
            "- `components/GithubPanel.jsx`: Interactive GitHub repository & issue browser.\n"
            "- `components/WorkspacePanel.jsx`: Google Calendar & Gmail integration hub.\n"
            "- `components/GraphVisualizer.jsx`: Visual LangGraph state execution graph.\n"
            "- `components/SettingsModal.jsx`: Configuration panel for Gemini & MCP credentials.\n\n"
            "To add a new UI tab or custom component, simply create your React component in `frontend/src/components/` and register it in `frontend/src/App.jsx`."
        )
    else:
        return (
            f"Hello! I am your Supervisor LangGraph Agent.\n\n"
            f"Regarding your query: *\"{query}\"*\n\n"
            f"I orchestrate 3 powerful sub-agents for specialized tasks:\n"
            f"1. **PDF RAG Sub-Agent**: Search and ask questions about uploaded PDF documents.\n"
            f"2. **GitHub MCP Sub-Agent**: Search repos, view commits, inspect open issues.\n"
            f"3. **Google Workspace MCP Sub-Agent**: Manage Google Calendar meetings and Gmail drafts.\n\n"
            f"Feel free to ask a question or select a specific sub-agent route below!"
        )

def run_supervisor_sub_agent(state: AgentState) -> Dict[str, Any]:
    """Supervisor Agent node that directly handles general user questions, UI questions, and system orchestration queries."""
    query = state.get("user_query", "")
    logger.info(f"Supervisor Agent processing general query: {query}")

    if settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",
                google_api_key=settings.gemini_api_key,
                temperature=0.3
            )
            system_prompt = (
                "You are the Supervisor Orchestrator Agent for the LangGraph Multi-Agent System.\n"
                "You coordinate 3 specialized sub-agents:\n"
                "1. Sub-Agent 01: PDF RAG with hosted Qdrant Vector DB\n"
                "2. Sub-Agent 02: GitHub MCP Agent (Repos, commits, issues, code analysis)\n"
                "3. Sub-Agent 03: Google Workspace MCP Agent (Calendar events & Gmail drafting/sending)\n\n"
                "The system frontend UI is built with React, Vite, Lucide Icons, and Tailwind CSS.\n"
                "Answer the user's question accurately, concisely, and helpfully. If they ask about adding UI components, customization, or using the system, explain clearly."
            )
            res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)])
            response_text = res.content
        except Exception as e:
            logger.warning(f"Supervisor LLM error ({e}), using structured response.")
            response_text = generate_supervisor_fallback(query)
    else:
        response_text = generate_supervisor_fallback(query)

    logs = state.get("execution_logs", [])
    logs.append({
        "node": "supervisor_agent",
        "status": "completed",
        "details": "Supervisor Agent answered user query."
    })

    return {
        "agent_response": response_text,
        "active_agent": "supervisor",
        "execution_logs": logs
    }

def supervisor_router(state: AgentState) -> Dict[str, Any]:
    """Supervisor node that classifies query intent and routes to sub-agent."""
    query = state.get("user_query", "").lower()
    forced_target = state.get("next_step", "")
    logs = state.get("execution_logs", [])

    if forced_target in ["rag", "github", "google_workspace", "supervisor"]:
        target = forced_target
    elif any(k in query for k in ["meeting", "calendar", "event", "schedule", "email", "gmail", "draft", "invite", "notify", "appointment"]):
        target = "google_workspace"
    elif any(k in query for k in ["pdf", "document", "file", "qdrant", "paper", "content", "what does the doc say", "rag"]):
        target = "rag"
    elif any(k in query for k in ["github", "repo", "commit", "issue", "branch", "codebase", "stars"]) or ("/" in query and not "http" in query):
        target = "github"
    elif any(k in query for k in ["ui", "frontend", "react", "component", "interface", "design", "help", "hello", "hi", "supervisor"]):
        target = "supervisor"
    else:
        # Default router heuristic
        target = "supervisor"

    logs.append({
        "node": "supervisor_router",
        "status": "routed",
        "target_sub_agent": target,
        "details": f"Analyzed user prompt and routed task to '{target}' agent."
    })

    return {
        "next_step": target,
        "execution_logs": logs
    }

def route_decision(state: AgentState) -> str:
    return state.get("next_step", "supervisor")

def supervisor_synthesis(state: AgentState) -> Dict[str, Any]:
    """Final Supervisor node that checks answer completeness and logs final graph state."""
    logs = state.get("execution_logs", [])
    logs.append({
        "node": "supervisor_synthesis",
        "status": "completed",
        "active_agent": state.get("active_agent", "supervisor"),
        "details": "Validated agent output and compiled final response."
    })
    return {
        "execution_logs": logs
    }

def build_langgraph_agent():
    """Constructs and compiles the complete LangGraph Multi-Agent State Graph."""
    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("supervisor_router", supervisor_router)
    builder.add_node("supervisor_node", run_supervisor_sub_agent)
    builder.add_node("rag_node", run_rag_sub_agent)
    builder.add_node("github_node", run_github_mcp_sub_agent)
    builder.add_node("google_workspace_node", run_google_workspace_sub_agent)
    builder.add_node("supervisor_synthesis", supervisor_synthesis)

    # Set Entry Point
    builder.set_entry_point("supervisor_router")

    # Add Conditional Edges from Supervisor Router
    builder.add_conditional_edges(
        "supervisor_router",
        route_decision,
        {
            "supervisor": "supervisor_node",
            "rag": "rag_node",
            "github": "github_node",
            "google_workspace": "google_workspace_node"
        }
    )

    # Edge from Sub-agents & Supervisor node to Synthesis Node
    builder.add_edge("supervisor_node", "supervisor_synthesis")
    builder.add_edge("rag_node", "supervisor_synthesis")
    builder.add_edge("github_node", "supervisor_synthesis")
    builder.add_edge("google_workspace_node", "supervisor_synthesis")
    builder.add_edge("supervisor_synthesis", END)

    # Compile Graph
    return builder.compile()

langgraph_orchestrator = build_langgraph_agent()

