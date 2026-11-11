"""
ingest.py
Run this script once to process all PDFs, create embeddings via Gemini,
and build the FAISS index on your D: drive.
"""
from app.rag_engine import get_rag_engine

if __name__ == "__main__":
    print("Initializing BiztelAI Copilot Ingestion Pipeline...")
    engine = get_rag_engine()
    total_chunks = engine.build_and_save_index()
    print(f"Ingestion complete! Successfully indexed {total_chunks} chunks into FAISS.")