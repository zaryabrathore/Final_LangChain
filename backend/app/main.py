import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.config import settings
from app.vectorstore.qdrant_service import qdrant_service
from app.mcp.github_mcp_client import github_mcp_client
from app.mcp.google_mcp_client import google_mcp_client
from app.graph.workflow import langgraph_orchestrator

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("langgraph_server")

app = FastAPI(
    title="LangGraph Multi-Agent System API",
    description="Orchestrated LangGraph Agents with Hosted Qdrant RAG, GitHub MCP, and Google Workspace (Calendar & Gmail) MCP Sub-Agents",
    version="1.0.0"
)

# CORS configuration for React Vite frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    user_query: str
    target_sub_agent: Optional[str] = None  # "rag", "github", "google_workspace", or None for auto-supervisor

class SettingsUpdateRequest(BaseModel):
    gemini_api_key: Optional[str] = None
    qdrant_host: Optional[str] = None
    qdrant_api_key: Optional[str] = None
    qdrant_collection: Optional[str] = None
    github_token: Optional[str] = None
    google_user_email: Optional[str] = None

class MCPExecuteRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any]

@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "system": "LangGraph Multi-Agent System",
        "settings": settings.to_dict()
    }

@app.get("/api/settings")
def get_settings():
    return settings.to_dict()

@app.post("/api/settings")
def update_settings(req: SettingsUpdateRequest):
    update_data = {k: v for k, v in req.model_dump().items() if v is not None}
    settings.update(update_data)
    return {"status": "success", "updated": list(update_data.keys()), "current_settings": settings.to_dict()}

@app.post("/api/rag/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
    
    try:
        contents = await file.read()
        res = qdrant_service.process_and_store_pdf(contents, file.filename)
        return {"status": "success", "message": f"PDF '{file.filename}' processed and stored in hosted Qdrant vector store.", "metadata": res}
    except Exception as e:
        logger.error(f"Error uploading PDF: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/documents")
def list_indexed_documents():
    return {"documents": qdrant_service.get_indexed_documents()}

@app.post("/api/agent/query")
def query_agent(req: QueryRequest):
    """Executes prompt through the LangGraph Orchestrator Graph."""
    try:
        initial_state = {
            "user_query": req.user_query,
            "messages": [{"role": "user", "content": req.user_query}],
            "next_step": req.target_sub_agent or "",
            "active_agent": "supervisor",
            "rag_context": [],
            "github_result": None,
            "google_result": None,
            "agent_response": "",
            "execution_logs": []
        }

        final_state = langgraph_orchestrator.invoke(initial_state)

        return {
            "status": "success",
            "user_query": req.user_query,
            "active_agent": final_state.get("active_agent"),
            "agent_response": final_state.get("agent_response"),
            "rag_context": final_state.get("rag_context", []),
            "github_result": final_state.get("github_result"),
            "google_result": final_state.get("google_result"),
            "execution_logs": final_state.get("execution_logs", [])
        }
    except Exception as e:
        logger.error(f"Error executing LangGraph agent: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/mcp/github/tools")
def get_github_mcp_tools():
    return {"tools": github_mcp_client.get_mcp_tool_definitions()}

@app.post("/api/mcp/github/execute")
def execute_github_mcp(req: MCPExecuteRequest):
    res = github_mcp_client.execute_mcp_tool(req.tool_name, req.arguments)
    return {"tool_name": req.tool_name, "result": res}

@app.get("/api/mcp/google/tools")
def get_google_mcp_tools():
    return {"tools": google_mcp_client.get_mcp_tool_definitions()}

@app.post("/api/mcp/google/execute")
def execute_google_mcp(req: MCPExecuteRequest):
    res = google_mcp_client.execute_mcp_tool(req.tool_name, req.arguments)
    return {"tool_name": req.tool_name, "result": res}

@app.websocket("/ws/agent")
async def websocket_agent_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            user_query = data.get("user_query", "")
            target_sub_agent = data.get("target_sub_agent", "")

            await websocket.send_json({"type": "node_start", "node": "supervisor_router", "message": "Analyzing prompt intent..."})

            initial_state = {
                "user_query": user_query,
                "messages": [{"role": "user", "content": user_query}],
                "next_step": target_sub_agent,
                "active_agent": "supervisor",
                "rag_context": [],
                "github_result": None,
                "google_result": None,
                "agent_response": "",
                "execution_logs": []
            }

            # Run orchestrator
            final_state = langgraph_orchestrator.invoke(initial_state)

            active_agent = final_state.get("active_agent", "supervisor")
            await websocket.send_json({"type": "node_complete", "node": active_agent, "logs": final_state.get("execution_logs", [])})

            await websocket.send_json({
                "type": "final_result",
                "active_agent": active_agent,
                "agent_response": final_state.get("agent_response"),
                "rag_context": final_state.get("rag_context", []),
                "github_result": final_state.get("github_result"),
                "google_result": final_state.get("google_result"),
                "execution_logs": final_state.get("execution_logs", [])
            })
    except WebSocketDisconnect:
        logger.info("WebSocket disconnected")
