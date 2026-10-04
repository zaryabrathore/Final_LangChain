import logging
from typing import Dict, Any
from app.mcp.github_mcp_client import github_mcp_client
from app.config import settings

logger = logging.getLogger(__name__)

def run_github_mcp_sub_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Sub-Agent 02: GitHub MCP Sub-Agent for asking questions about GitHub repositories."""
    query = state.get("user_query", "").lower()
    logger.info(f"GitHub MCP Sub-Agent processing query: {query}")

    # Determine tool selection based on intent
    if "commit" in query or "log" in query or "history" in query:
        tool_name = "github_list_commits"
        args = {"owner": "langchain-ai", "repo": "langgraph", "limit": 5}
    elif "issue" in query or "bug" in query or "pr" in query:
        tool_name = "github_list_issues"
        args = {"owner": "langchain-ai", "repo": "langgraph", "state": "open"}
    elif "file" in query or "read" in query or "code" in query or "readme" in query:
        tool_name = "github_read_file"
        args = {"owner": "langchain-ai", "repo": "langgraph", "path": "README.md"}
    elif "/" in query and not " " in query:
        parts = query.strip().split("/")
        tool_name = "github_get_repository"
        args = {"owner": parts[0], "repo": parts[1]}
    else:
        tool_name = "github_search_repositories"
        clean_q = query.replace("github", "").replace("search", "").replace("repo", "").strip()
        args = {"query": clean_q if clean_q else "langgraph"}

    mcp_res = github_mcp_client.execute_mcp_tool(tool_name, args)

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
                f"You are the GitHub MCP Sub-Agent. Answer the user's question using the raw GitHub MCP tool output below.\n\n"
                f"User Question: {state.get('user_query')}\n\n"
                f"GitHub MCP Executed Tool: {tool_name}\n"
                f"GitHub MCP Output: {mcp_res}\n\n"
                f"Format your response nicely with markdown links, bullet points, and code blocks."
            )
            res = llm.invoke([HumanMessage(content=prompt)])
            response_text = res.content
        except Exception as e:
            logger.warning(f"Gemini LLM GitHub MCP invocation error: {e}")
            response_text = f"**GitHub MCP Sub-Agent Result ({tool_name})**:\n\n```json\n{mcp_res}\n```"
    else:
        if tool_name == "github_search_repositories":
            repos = mcp_res.get("repositories", [])
            repo_lines = [f"- [{r['full_name']}]({r['url']}) - ⭐ {r['stars']} stars: {r['description']}" for r in repos]
            response_text = f"**GitHub MCP Search Results for query:**\n\n" + "\n".join(repo_lines)
        elif tool_name == "github_list_commits":
            commits = mcp_res.get("commits", [])
            commit_lines = [f"- `[{c['sha']}]` {c['message']} (by **{c['author']}**)" for c in commits]
            response_text = f"**GitHub MCP Recent Commit Logs:**\n\n" + "\n".join(commit_lines)
        elif tool_name == "github_list_issues":
            issues = mcp_res.get("issues", [])
            issue_lines = [f"- #{i['number']} **{i['title']}** (Author: {i['user']})" for i in issues]
            response_text = f"**GitHub MCP Open Issues:**\n\n" + "\n".join(issue_lines)
        else:
            response_text = f"**GitHub MCP Tool Output (`{tool_name}`):**\n\n{mcp_res}"

    logs = state.get("execution_logs", [])
    logs.append({
        "node": "github_mcp_sub_agent",
        "status": "completed",
        "mcp_tool": tool_name,
        "details": f"Executed GitHub MCP tool '{tool_name}' with args {args}."
    })

    return {
        "github_result": mcp_res,
        "agent_response": response_text,
        "active_agent": "github_mcp_sub_agent",
        "execution_logs": logs
    }
