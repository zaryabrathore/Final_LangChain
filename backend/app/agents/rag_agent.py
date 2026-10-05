import logging
from typing import Dict, Any
from app.vectorstore.qdrant_service import qdrant_service
from app.config import settings

logger = logging.getLogger(__name__)

def run_rag_sub_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph Sub-Agent 01: Complete PDF RAG with hosted Qdrant vector store."""
    query = state.get("user_query", "")
    logger.info(f"RAG Sub-Agent processing query: {query}")

    # 1. Search hosted Qdrant Vector DB
    search_results = qdrant_service.search_similar(query, top_k=4)

    if not search_results:
        context_str = "No indexed PDF documents found in Qdrant vector store."
        response_text = "I searched the hosted Qdrant vector database, but no indexed PDF documents were found. Please upload a PDF document first using the PDF RAG panel."
    else:
        context_chunks = []
        for idx, res in enumerate(search_results):
            context_chunks.append(f"--- Document: {res['filename']} (Page {res['page']}) [Relevance Score: {res['score']:.2f}] ---\n{res['text']}")
        
        context_str = "\n\n".join(context_chunks)

        if settings.gemini_api_key:
            try:
                from langchain_google_genai import ChatGoogleGenerativeAI
                from langchain_core.messages import SystemMessage, HumanMessage

                llm = ChatGoogleGenerativeAI(
                    model="gemini-1.5-flash-latest",
                    google_api_key=settings.gemini_api_key,
                    temperature=0.2
                )
                prompt = (
                    f"You are the RAG Sub-Agent. Answer the user's question based strictly on the retrieved PDF document excerpts below.\n"
                    f"Always cite the filename and page numbers in your answer.\n\n"
                    f"Retrieved Context:\n{context_str}\n\n"
                    f"User Question: {query}"
                )
                res = llm.invoke([HumanMessage(content=prompt)])
                response_text = res.content
            except Exception as e:
                logger.warning(f"Gemini LLM RAG invocation error: {e}")
                if search_results:
                    response_text = f"Based on retrieved context from `{search_results[0]['filename']}` (Page {search_results[0]['page']}):\n\n" \
                                    f"{search_results[0]['text'][:300]}..."
                else:
                    response_text = "No relevant PDF context found for your query."
        else:
            top_doc = search_results[0]
            response_text = f"**RAG Sub-Agent Answer** (Source: `{top_doc['filename']}`, Page {top_doc['page']}):\n\n" \
                            f"{top_doc['text']}\n\n" \
                            f"*(Note: Provide a Gemini API Key in Settings for full LLM generative synthesis)*"

    logs = state.get("execution_logs", [])
    logs.append({
        "node": "rag_sub_agent",
        "status": "completed",
        "retrieved_chunks": len(search_results),
        "details": f"Queried Qdrant hosted vector store and retrieved {len(search_results)} relevant document chunks."
    })

    return {
        "rag_context": search_results,
        "agent_response": response_text,
        "active_agent": "rag_sub_agent",
        "execution_logs": logs
    }
