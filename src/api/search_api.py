"""FastAPI server for RAG search"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from config import Config
from src.embeddings import GeminiEmbedder
from src.vector_store import ChromaStore

app = FastAPI(
    title="RAG Search API",
    description="API for searching documents using RAG",
    version="1.0.0"
)

# Enable CORS for web chatbot
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your chatbot domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for embedder and vector store
embedder: Optional[GeminiEmbedder] = None
vector_store: Optional[ChromaStore] = None


class SearchRequest(BaseModel):
    query: str
    top_k: int = 10  # Increased from 5 to 10 for better coverage


class SearchResponse(BaseModel):
    results: List[Dict]
    query: str


class HealthResponse(BaseModel):
    status: str
    vector_store_count: int


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global embedder, vector_store

    try:
        Config.validate()
        embedder = GeminiEmbedder(api_key=Config.GOOGLE_API_KEY)
        vector_store = ChromaStore(
            persist_directory=Config.CHROMA_DB_PATH,
            collection_name="documents"
        )
        print("✓ Services initialized successfully")
    except Exception as e:
        print(f"✗ Error initializing services: {e}")
        raise


@app.get("/", response_model=Dict)
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Search API",
        "version": "1.0.0",
        "endpoints": {
            "search": "/search",
            "health": "/health",
            "info": "/info"
        }
    }


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    info = vector_store.get_collection_info()
    return {
        "status": "healthy",
        "vector_store_count": info['count']
    }


@app.get("/info", response_model=Dict)
async def get_info():
    """Get vector store information"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    return vector_store.get_collection_info()


@app.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    Search for relevant documents

    Args:
        request: SearchRequest with query and top_k

    Returns:
        SearchResponse with results
    """
    if embedder is None or vector_store is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Generate query embedding
        query_embedding = embedder.embed_query(request.query)

        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Search vector store
        results = vector_store.search(query_embedding, top_k=request.top_k)

        # Format results
        formatted_results = []
        for i in range(len(results['documents'])):
            formatted_results.append({
                'text': results['documents'][i],
                'metadata': results['metadatas'][i],
                'score': 1 - results['distances'][i]  # Convert distance to similarity score
            })

        return {
            "query": request.query,
            "results": formatted_results
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")


@app.post("/chat", response_model=Dict)
async def chat(request: SearchRequest):
    """
    Chat endpoint that returns context for the chatbot

    Args:
        request: SearchRequest with query and top_k

    Returns:
        Context and documents for chatbot to use
    """
    if embedder is None or vector_store is None:
        raise HTTPException(status_code=503, detail="Services not initialized")

    try:
        # Generate query embedding
        query_embedding = embedder.embed_query(request.query)

        if not query_embedding:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")

        # Search vector store
        results = vector_store.search(query_embedding, top_k=request.top_k)

        # Log search quality
        print(f"\n🔍 Search Query: {request.query}")
        print(f"📊 Requested top_k: {request.top_k}")
        print(f"📝 Results found: {len(results['documents'])}")

        # Filter results by distance threshold (optional quality filter)
        # Distance ranges: 0.0 (identical) to 2.0 (very different)
        # Keep results with distance < 1.5 (reasonably similar)
        MAX_DISTANCE = 1.5
        filtered_results = {
            'documents': [],
            'metadatas': [],
            'distances': []
        }

        for i in range(len(results['documents'])):
            distance = results['distances'][i]
            if distance < MAX_DISTANCE:
                filtered_results['documents'].append(results['documents'][i])
                filtered_results['metadatas'].append(results['metadatas'][i])
                filtered_results['distances'].append(distance)

        print(f"✅ After filtering (distance < {MAX_DISTANCE}): {len(filtered_results['documents'])} results")

        # Log top results
        for i in range(min(3, len(filtered_results['documents']))):
            source = filtered_results['metadatas'][i].get('source', 'Unknown')
            distance = filtered_results['distances'][i]
            print(f"   [{i+1}] {source} (distance: {distance:.4f})")

        # Use filtered results
        results = filtered_results

        # Create context from results
        context_parts = []
        for i, doc in enumerate(results['documents'], 1):
            context_parts.append(f"[문서 {i}]\n{doc}\n")

        context = "\n".join(context_parts)

        # Extract unique sources with confidence scores
        sources = []
        seen = set()
        source_details = []
        for i in range(len(results['metadatas'])):
            source = results['metadatas'][i].get('source', 'Unknown')
            distance = results['distances'][i]
            # Ensure source is a string
            if isinstance(source, dict):
                source = source.get('name', 'Unknown')
            source_str = str(source)
            if source_str not in seen:
                sources.append(source_str)
                seen.add(source_str)
                # Add confidence score (1 - normalized distance)
                confidence = max(0, 1 - (distance / 2.0))
                source_details.append({
                    'file': source_str,
                    'confidence': round(confidence, 2),
                    'distance': round(distance, 4)
                })

        return {
            "query": request.query,
            "context": context,
            "source_count": len(results['documents']),
            "sources": sources,
            "source_details": source_details,
            "total_results": len(results['documents'])
        }

    except Exception as e:
        print(f"❌ Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")
