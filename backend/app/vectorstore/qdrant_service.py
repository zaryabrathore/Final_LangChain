import io
import uuid
import logging
from typing import List, Dict, Any, Optional
from qdrant_client import QdrantClient
from qdrant_client.http import models as rest_models
from langchain_text_splitters import RecursiveCharacterTextSplitter
from pypdf import PdfReader
from app.config import settings

logger = logging.getLogger(__name__)

class QdrantVectorService:
    def __init__(self):
        self._client: Optional[QdrantClient] = None
        self.documents_metadata: List[Dict[str, Any]] = []

    def get_client(self) -> QdrantClient:
        if settings.qdrant_host and settings.qdrant_api_key:
            logger.info(f"Connecting to hosted Qdrant Cloud at {settings.qdrant_host}")
            return QdrantClient(url=settings.qdrant_host, api_key=settings.qdrant_api_key)
        else:
            logger.info("Using local in-memory Qdrant instance")
            if not self._client:
                self._client = QdrantClient(location=":memory:")
            return self._client

    def _ensure_collection(self, client: QdrantClient, vector_size: int = 768):
        collection_name = settings.qdrant_collection
        collections = client.get_collections().collections
        exists = any(c.name == collection_name for c in collections)
        if not exists:
            client.create_collection(
                collection_name=collection_name,
                vectors_config=rest_models.VectorParams(
                    size=vector_size,
                    distance=rest_models.Distance.COSINE
                )
            )

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generates embeddings using Google Gemini embeddings or deterministic feature vectors."""
        if settings.gemini_api_key:
            try:
                from langchain_google_genai import GoogleGenerativeAIEmbeddings
                embedder = GoogleGenerativeAIEmbeddings(
                    model="models/text-embedding-004",
                    google_api_key=settings.gemini_api_key
                )
                return embedder.embed_documents(texts)
            except Exception as e:
                logger.warning(f"Error using Gemini Embeddings API ({e}), falling back to deterministic vector generator.")
        
        # Fallback pseudo-embedding generator (768 dimensions for compatibility)
        embeddings = []
        for text in texts:
            vec = [0.0] * 768
            # Hash words into vector bins for deterministic similarity match
            words = text.lower().split()
            for idx, word in enumerate(words):
                h = abs(hash(word)) % 768
                vec[h] += 1.0 / (idx + 1)
            # Normalize
            norm = sum(x*x for x in vec) ** 0.5
            if norm > 0:
                vec = [x / norm for x in vec]
            embeddings.append(vec)
        return embeddings

    def process_and_store_pdf(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Loads PDF, splits text into chunks, computes embeddings, and stores in Qdrant vector store."""
        reader = PdfReader(io.BytesIO(file_bytes))
        pages_text = []
        for i, page in enumerate(reader.pages):
            txt = page.extract_text() or ""
            if txt.strip():
                pages_text.append({"page": i + 1, "text": txt})

        if not pages_text:
            raise ValueError(f"No extractable text found in PDF: {filename}")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=600,
            chunk_overlap=100
        )

        chunks = []
        for p in pages_text:
            sub_chunks = text_splitter.split_text(p["text"])
            for sc in sub_chunks:
                chunks.append({
                    "id": str(uuid.uuid4()),
                    "filename": filename,
                    "page": p["page"],
                    "text": sc
                })

        texts = [c["text"] for c in chunks]
        embeddings = self.generate_embeddings(texts)
        vector_dim = len(embeddings[0]) if embeddings else 768

        client = self.get_client()
        self._ensure_collection(client, vector_size=vector_dim)

        points = []
        for idx, c in enumerate(chunks):
            points.append(rest_models.PointStruct(
                id=c["id"],
                vector=embeddings[idx],
                payload={
                    "filename": c["filename"],
                    "page": c["page"],
                    "text": c["text"],
                    "chunk_id": c["id"]
                }
            ))

        client.upsert(
            collection_name=settings.qdrant_collection,
            points=points
        )

        doc_summary = {
            "filename": filename,
            "total_pages": len(reader.pages),
            "total_chunks": len(chunks),
            "status": "indexed_in_qdrant"
        }
        self.documents_metadata.append(doc_summary)
        return doc_summary

    def search_similar(self, query: str, top_k: int = 4) -> List[Dict[str, Any]]:
        """Performs vector similarity search in Qdrant for a given text query."""
        client = self.get_client()
        collection_name = settings.qdrant_collection
        
        try:
            collections = client.get_collections().collections
            if not any(c.name == collection_name for c in collections):
                return []
        except Exception:
            return []

        query_vector = self.generate_embeddings([query])[0]
        
        # Search Qdrant
        search_results = client.search(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=top_k
        )

        results = []
        for hit in search_results:
            results.append({
                "score": float(hit.score),
                "filename": hit.payload.get("filename", "document.pdf"),
                "page": hit.payload.get("page", 1),
                "text": hit.payload.get("text", ""),
                "chunk_id": hit.payload.get("chunk_id", hit.id)
            })
        return results

    def get_indexed_documents(self) -> List[Dict[str, Any]]:
        return self.documents_metadata

qdrant_service = QdrantVectorService()
