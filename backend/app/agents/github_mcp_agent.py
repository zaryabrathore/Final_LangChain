import json
import logging
import re
from typing import Dict, Any
from app.mcp.github_mcp_client import github_mcp_client
from app.config import settings

logger = logging.getLogger(__name__)

def _extract_owner_repo(query: str) -> tuple[str, str]:
    """Extracts owner and repository name from query string if present."""
    match = re.search(r'([\w\.-]+)/([\w\.-]+)', query)
    if match:
        return match.group(1), match.group(2)
    return "ZaryabRathore", "Final_LangChain"

def run_github_mcp_sub_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Sub-Agent 02: GitHub MCP Sub-Agent."""
    query = state.get("user_query", "")
    query_lower = query.lower()
    logger.info(f"GitHub MCP Sub-Agent processing query: {query}")

    tool_name = None
    args = {}

    # 1. Try Gemini LLM for dynamic tool & argument extraction
    if settings.gemini_api_key:
        try:
            from langchain_google_genai import ChatGoogleGenerativeAI
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGoogleGenerativeAI(
                model="gemini-1.5-flash-latest",
                google_api_key=settings.gemini_api_key,
                temperature=0.1
            )
            tools_schema = json.dumps(github_mcp_client.get_mcp_tool_definitions(), indent=2)

            system_prompt = (
                f"You are the Tool Dispatcher for GitHub MCP.\n"
                f"Available MCP Tools Schema:\n{tools_schema}\n\n"
                f"Your task: Determine the single best GitHub MCP tool to execute for the user query and construct its arguments.\n"
                f"Respond ONLY with valid JSON in this exact structure without markdown backticks:\n"
                f'{{"tool_name": "<name>", "arguments": {{...}}}}\n\n'
                f"Default fallback owner/repo if not specified in prompt: 'ZaryabRathore' / 'Final_LangChain'."
            )
            res = llm.invoke([SystemMessage(content=system_prompt), HumanMessage(content=query)])
            cleaned_text = res.content.strip().replace("```json", "").replace("```", "").strip()
            parsed = json.loads(cleaned_text)

            if "tool_name" in parsed and "arguments" in parsed:
                tool_name = parsed["tool_name"]
                args = parsed["arguments"]
                logger.info(f"Gemini GitHub tool resolution: {tool_name} with args {args}")
        except Exception as e:
            logger.warning(f"Gemini GitHub tool dispatch error ({e}), using heuristic parser.")

    # 2. Heuristic fallback
    if not tool_name:
        owner, repo = _extract_owner_repo(query)
        if "commit" in query_lower or "log" in query_lower or "history" in query_lower:
            tool_name = "github_list_commits"
            args = {"owner": owner, "repo": repo, "limit": 5}
        elif "issue" in query_lower or "bug" in query_lower or "pr" in query_lower:
            tool_name = "github_list_issues"
            args = {"owner": owner, "repo": repo, "state": "open"}
        elif "file" in query_lower or "read" in query_lower or "code" in query_lower or "readme" in query_lower:
            tool_name = "github_read_file"
            args = {"owner": owner, "repo": repo, "path": "README.md"}
        elif "/" in query and not " " in query:
            tool_name = "github_get_repository"
            args = {"owner": owner, "repo": repo}
        else:
            tool_name = "github_search_repositories"
            clean_q = re.sub(r'\b(github|search|repositories|repository|repos|repo|find|for|look for|show)\b', '', query, flags=re.IGNORECASE).strip()
            args = {"query": clean_q if clean_q else repo}

    # Execute GitHub MCP Tool
    mcp_res = github_mcp_client.execute_mcp_tool(tool_name, args)

    # Synthesize AI Response
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
                f"You are the GitHub MCP Sub-Agent. Answer the user request using the raw GitHub MCP tool output below.\n\n"
                f"User Question: {query}\n"
                f"Executed MCP Tool: {tool_name}\n"
                f"MCP Tool Arguments: {json.dumps(args)}\n"
                f"MCP Output Data: {json.dumps(mcp_res)}\n\n"
                f"Format your response nicely with markdown links, bullet points, and code blocks."
            )
            res = llm.invoke([HumanMessage(content=prompt)])
            response_text = res.content
        except Exception as e:
            logger.warning(f"Gemini LLM GitHub MCP invocation error: {e}")
            response_text = f"**GitHub MCP Result (`{tool_name}`)**:\n\n```json\n{json.dumps(mcp_res, indent=2)}\n```"
    else:
        if tool_name == "github_search_repositories":
            repos = mcp_res.get("repositories", [])
            repo_lines = [f"- [{r.get('full_name')}]({r.get('url')}) - ⭐ {r.get('stars', 0)} stars: {r.get('description', '')}" for r in repos]
            response_text = f"**GitHub MCP Search Results:**\n\n" + "\n".join(repo_lines)
        elif tool_name == "github_list_commits":
            commits = mcp_res.get("commits", [])
            commit_lines = [f"- `[{c.get('sha')}]` {c.get('message')} (by **{c.get('author')}** on `{c.get('date', 'N/A')}`)" for c in commits]
            response_text = f"**GitHub Recent Commits ({args.get('owner')}/{args.get('repo')}):**\n\n" + "\n".join(commit_lines)
        elif tool_name == "github_list_issues":
            issues = mcp_res.get("issues", [])
            issue_lines = [f"- #{i.get('number')} **{i.get('title')}** (Author: {i.get('user')})" for i in issues]
            response_text = f"**GitHub Open Issues ({args.get('owner')}/{args.get('repo')}):**\n\n" + "\n".join(issue_lines)
        else:
            response_text = f"**GitHub MCP Tool Output (`{tool_name}`):**\n\n```json\n{json.dumps(mcp_res, indent=2)}\n```"

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

