"""
app/main.py
FastAPI backend application for the BiztelAI Manufacturing AI Copilot.
Handles question queries, RAG generation, and serves the static frontend UI.
"""
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import STATIC_DIR
from app.rag_engine import get_rag_engine

app = FastAPI(
    title="BiztelAI Manufacturing AI Copilot",
    description="RAG-powered AI assistant for factory supervisors and operators at Kaveri Precision Components.",
    version="1.0.0"
)

# Enable CORS for local testing and mobile access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic Request Model
class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=2, description="The supervisor's question about plant SOPs or manuals.")


@app.get("/api/health")
def health_check():
    """Health check endpoint to verify server status."""
    return {"status": "healthy", "service": "BiztelAI Copilot API"}


@app.post("/api/ask")
def ask_copilot(payload: QuestionRequest):
    """
    Main RAG endpoint. Receives a supervisor's question, retrieves relevant PDF chunks,
    and returns a grounded AI answer with citations and revision warnings.
    """
    try:
        engine = get_rag_engine()
        result = engine.answer_question(payload.question)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Mount the static directory to serve the frontend UI at the root URL (/)
if STATIC_DIR.exists():
    app.mount("/", StaticFiles(directory=str(STATIC_DIR), html=True), name="static")
else:
    @app.get("/")
    def root_fallback():
        return {"message": "FastAPI backend is running, but static/ folder was not found."}