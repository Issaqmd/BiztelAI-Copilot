"""
app/rag_engine.py
Handles FAISS vector indexing, Gemini embeddings, local similarity search,
and strict grounded answer generation using direct REST API calls (bypassing Python 3.14 SSL/httpx timeouts).
"""
import json
import time
import urllib.request
from typing import List, Dict, Any
import numpy as np
import faiss

from app.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    EMBEDDING_MODEL,
    FAISS_INDEX_PATH,
    CHUNKS_METADATA_PATH,
    TOP_K_RESULTS,
)
from app.pdf_processor import load_and_chunk_pdfs


class RAGEngine:
    def __init__(self):
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is missing or empty in .env file!")

        self.index = None
        self.chunks_metadata: List[Dict[str, Any]] = []
        self.load_local_index()

    def get_embedding(self, text: str) -> List[float]:
        """
        Generates a vector embedding for a piece of text using Google Gemini Embedding REST API
        with a 15-second timeout (bypassing Python 3.14 SSL/httpx socket issues).
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBEDDING_MODEL}:embedContent?key={GEMINI_API_KEY}"
        
        payload = {
            "model": f"models/{EMBEDDING_MODEL}",
            "content": {
                "parts": [{"text": text}]
            }
        }
        
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            # REST embedding response returns {"embedding": {"values": [...]}}
            return res_json.get("embedding", {}).get("values", [])

    def build_and_save_index(self) -> int:
        """
        Ingests PDFs, generates embeddings, builds FAISS index, and saves to disk.
        """
        print("Starting PDF ingestion and chunking...")
        chunks = load_and_chunk_pdfs()
        if not chunks:
            raise ValueError("No chunks found to index!")

        print(f"Generated {len(chunks)} chunks. Generating embeddings via Gemini API...")
        embeddings = []
        for i, chunk in enumerate(chunks, 1):
            print(f"Embedding chunk {i}/{len(chunks)} ({chunk['doc_id']} Page {chunk['page_number']})...")
            vector = self.get_embedding(chunk["contextualized_text"])
            if not vector:
                raise ValueError(f"Failed to generate embedding for chunk {i}")
            embeddings.append(vector)

        dimension = len(embeddings[0])
        embeddings_matrix = np.array(embeddings, dtype=np.float32)

        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings_matrix)

        faiss.write_index(index, str(FAISS_INDEX_PATH))

        with open(CHUNKS_METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(chunks, f, indent=2, ensure_ascii=False)

        self.index = index
        self.chunks_metadata = chunks
        print(f"SUCCESS: FAISS index built and saved with {len(chunks)} vectors.")
        return len(chunks)

    def load_local_index(self) -> bool:
        """
        Loads pre-built FAISS index and chunk metadata from disk if available.
        """
        if FAISS_INDEX_PATH.exists() and CHUNKS_METADATA_PATH.exists():
            try:
                self.index = faiss.read_index(str(FAISS_INDEX_PATH))
                with open(CHUNKS_METADATA_PATH, "r", encoding="utf-8") as f:
                    self.chunks_metadata = json.load(f)
                return True
            except Exception as e:
                print(f"Warning: Could not load local index ({e}). Rebuilding...")
        return False

    def retrieve(self, query: str, top_k: int = TOP_K_RESULTS) -> List[Dict[str, Any]]:
        """
        Searches the FAISS index for the top_k most relevant chunks matching the query.
        """
        if self.index is None or not self.chunks_metadata:
            self.build_and_save_index()

        print(f"[RAG] Embedding question: '{query[:60]}...'")
        query_vector = np.array([self.get_embedding(query)], dtype=np.float32)
        distances, indices = self.index.search(query_vector, min(top_k, len(self.chunks_metadata)))

        retrieved = []
        for rank, idx in enumerate(indices[0]):
            if idx == -1 or idx >= len(self.chunks_metadata):
                continue
            chunk = self.chunks_metadata[idx].copy()
            chunk["similarity_score"] = float(distances[0][rank])
            retrieved.append(chunk)

        return retrieved

    def generate_answer_via_rest(self, prompt: str, system_instruction: str, model_name: str = "gemini-3.5-flash") -> str:
        """
        Calls Gemini generation via direct REST API using urllib with a 15-second timeout.
        """
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={GEMINI_API_KEY}"
        
        full_text = f"SYSTEM INSTRUCTION:\n{system_instruction}\n\nPROMPT:\n{prompt}"
        
        payload = {
            "contents": [{
                "parts": [{"text": full_text}]
            }],
            "generationConfig": {
                "temperature": 0.1,
                "maxOutputTokens": 2048
            }
        }
        
        req_data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=req_data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        
        with urllib.request.urlopen(req, timeout=15) as response:
            res_body = response.read().decode("utf-8")
            res_json = json.loads(res_body)
            
            candidates = res_json.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        
        return ""

    def answer_question(self, question: str) -> Dict[str, Any]:
        """
        Retrieves relevant PDF chunks and generates a grounded answer via REST API.
        """
        start_time = time.time()
        retrieved_chunks = self.retrieve(question, top_k=TOP_K_RESULTS)

        context_blocks = []
        sources_meta = []
        seen_sources = set()

        for chunk in retrieved_chunks:
            context_blocks.append(chunk["contextualized_text"])

            source_key = (chunk["doc_id"], chunk["revision"], chunk["page_number"])
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources_meta.append({
                    "doc_id": chunk["doc_id"],
                    "title": chunk["title"],
                    "revision": chunk["revision"],
                    "effective_date": chunk["effective_date"],
                    "status": chunk["status"],
                    "filename": chunk["filename"],
                    "page_number": chunk["page_number"],
                    "raw_text": chunk["raw_text"][:350] + "..." if len(chunk["raw_text"]) > 350 else chunk["raw_text"]
                })

        combined_context = "\n\n---\n\n".join(context_blocks)

        system_instruction = (
            "You are an expert Manufacturing AI Copilot assisting factory supervisors and operators "
            "at Kaveri Precision Components Pvt. Ltd., Hosur Plant. "
            "Your answers must be strictly grounded in the provided plant documents.\n\n"
            "CRITICAL RULES:\n"
            "1. Answer the question using ONLY the provided document context.\n"
            "2. If the answer cannot be found in the provided documents, you MUST state clearly: "
            "\"I cannot find this information in the provided plant manuals or procedures.\"\n"
            "3. Always cite your sources explicitly, mentioning the Document ID, Revision number, and Page number.\n"
            "4. REVISION WARNING: Pay strict attention to document statuses. If a document chunk is marked as SUPERSEDED, "
            "warn the user that it is obsolete and provide the active procedure instructions instead.\n"
            "5. Include safety callouts or authorized roles (Operator, Maintenance Technician, Shift Supervisor, "
            "Production Manager, Safety Officer, SQE) when relevant.\n"
            "6. Keep your tone concise, direct, and actionable for a busy factory supervisor."
        )

        prompt = (
            f"REFERENCE DOCUMENTS:\n{combined_context}\n\n"
            f"SUPERVISOR QUESTION: {question}\n\n"
            f"Provide a clear, professional, cited answer based strictly on the reference documents above."
        )

        models_to_try = [GEMINI_MODEL, "gemini-3.5-flash", "gemini-3.7-flash"]
        answer_text = ""
        last_error = None

        for model_name in models_to_try:
            if not model_name:
                continue
            try:
                print(f"[RAG] Generating answer using {model_name} (REST)...")
                answer_text = self.generate_answer_via_rest(prompt, system_instruction, model_name=model_name)
                if answer_text:
                    break
            except Exception as e:
                print(f"[RAG] Warning with {model_name}: {e}")
                last_error = e

        if not answer_text:
            answer_text = f"Error generating answer from Gemini API: {str(last_error)}"
            grounded = False
        else:
            grounded = "cannot find this information" not in answer_text.lower()

        elapsed = round(time.time() - start_time, 2)
        print(f"[RAG] Completed in {elapsed}s (Grounded: {grounded})")

        return {
            "question": question,
            "answer": answer_text,
            "grounded": grounded,
            "sources": sources_meta if grounded else []
        }


# Singleton instance for the app
_rag_engine_instance = None


def get_rag_engine() -> RAGEngine:
    global _rag_engine_instance
    if _rag_engine_instance is None:
        _rag_engine_instance = RAGEngine()
    return _rag_engine_instance