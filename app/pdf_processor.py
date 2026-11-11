"""
app/pdf_processor.py
Extracts text from factory PDFs using PyMuPDF, identifies document revision metadata
(automatically detecting superseded SOP revisions), and splits pages into overlapping chunks.
"""
import re
from pathlib import Path
from typing import List, Dict, Any
import pymupdf  # Modern import for PyMuPDF (replaces deprecated 'fitz')

from app.config import PDF_DIR, CHUNK_SIZE, CHUNK_OVERLAP


def extract_doc_metadata(first_page_text: str, filename: str) -> Dict[str, Any]:
    """
    Extracts Document No., Revision number, Title, and Effective Date from the PDF header.
    """
    # 1. Extract Document No. (e.g., MNT-MAN-CNC-02, QC-SOP-014, SAF-SOP-003)
    doc_id_match = re.search(r"([A-Z]{2,4}-[A-Z]{2,4}-[A-Z0-9-]+)", first_page_text)
    if not doc_id_match:
        doc_id_match = re.search(r"([A-Z]{2,4}-[A-Z]{2,4}-[A-Z0-9-]+)", filename)
    doc_id = doc_id_match.group(1) if doc_id_match else filename.replace(".pdf", "")

    # 2. Extract Revision number (e.g., 02, 03, 04, 05)
    rev_match = re.search(r"Revision\s*\n?\s*(\d+)", first_page_text, re.IGNORECASE)
    if not rev_match:
        rev_match = re.search(r"Rev(?:ision)?[\s_-]*(\d+)", first_page_text, re.IGNORECASE)
    if not rev_match:
        rev_match = re.search(r"Rev(\d+)", filename, re.IGNORECASE)
    revision_str = rev_match.group(1).zfill(2) if rev_match else "01"
    revision_num = int(revision_str)

    # 3. Extract Effective Date (e.g., 20-Jan-2026, 01-Jul-2026)
    date_match = re.search(
        r"Effective Date\s*\n?\s*([0-9]{1,2}\s*[-A-Za-z]+\s*[0-9]{4})",
        first_page_text,
        re.IGNORECASE,
    )
    effective_date = date_match.group(1).strip() if date_match else "Unknown"

    # 4. Extract Document Title (second line of header if available)
    lines = [line.strip() for line in first_page_text.splitlines() if line.strip()]
    title = lines[1] if len(lines) > 1 else filename

    return {
        "filename": filename,
        "doc_id": doc_id,
        "title": title,
        "revision": f"Rev {revision_str}",
        "revision_num": revision_num,
        "effective_date": effective_date,
    }


def clean_page_text(text: str) -> str:
    """
    Cleans extra blank lines and normalizes whitespace while preserving line breaks
    for tables and numbered procedures.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse 3+ consecutive newlines into 2 newlines
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def split_text_into_chunks(
    text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP
) -> List[str]:
    """
    Splits page text into overlapping chunks along paragraph/line boundaries
    so tables and numbered steps are not cut mid-line.
    """
    if len(text) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        end = min(start + chunk_size, text_length)

        # If we are not at the end of the text, try to break cleanly at a newline or period
        if end < text_length:
            newline_break = text.rfind("\n", start + int(chunk_size * 0.5), end)
            period_break = text.rfind(". ", start + int(chunk_size * 0.5), end)
            if newline_break != -1:
                end = newline_break + 1
            elif period_break != -1:
                end = period_break + 2

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= text_length:
            break

        start = max(end - chunk_overlap, start + 1)

    return chunks


def load_and_chunk_pdfs(pdf_dir: Path = PDF_DIR) -> List[Dict[str, Any]]:
    """
    Reads all PDFs in data/pdfs, detects which revisions are ACTIVE vs SUPERSEDED,
    and returns a list of enriched text chunks ready for embedding.
    """
    pdf_files = sorted(pdf_dir.glob("*.pdf"))
    if not pdf_files:
        raise FileNotFoundError(f"No PDF files found in {pdf_dir}")

    raw_docs = []
    highest_rev_by_doc_id: Dict[str, int] = {}

    # Pass 1: Read pages and find the highest revision number for each Document ID
    for pdf_path in pdf_files:
        # Ignore Sample_Questions.pdf if accidentally placed in data/pdfs
        if "sample_questions" in pdf_path.name.lower():
            continue

        doc = pymupdf.open(pdf_path)
        pages_data = []
        for page_index in range(len(doc)):
            page = doc[page_index]
            page_text = clean_page_text(page.get_text("text"))
            if page_text:
                pages_data.append({"page_number": page_index + 1, "text": page_text})
        doc.close()

        if not pages_data:
            continue

        meta = extract_doc_metadata(pages_data[0]["text"], pdf_path.name)
        doc_id = meta["doc_id"]
        rev_num = meta["revision_num"]

        if doc_id not in highest_rev_by_doc_id or rev_num > highest_rev_by_doc_id[doc_id]:
            highest_rev_by_doc_id[doc_id] = rev_num

        raw_docs.append({"meta": meta, "pages": pages_data})

    # Pass 2: Mark status (ACTIVE vs SUPERSEDED) and create chunks with context headers
    all_chunks: List[Dict[str, Any]] = []
    chunk_counter = 0

    for item in raw_docs:
        meta = item["meta"]
        doc_id = meta["doc_id"]
        rev_num = meta["revision_num"]
        max_rev = highest_rev_by_doc_id[doc_id]

        if rev_num < max_rev:
            status = f"SUPERSEDED (Obsolete - Superseded by {doc_id} Rev {str(max_rev).zfill(2)})"
            is_superseded = True
        else:
            status = "ACTIVE (Current Official Procedure)"
            is_superseded = False

        for page_info in item["pages"]:
            page_num = page_info["page_number"]
            raw_chunks = split_text_into_chunks(page_info["text"])

            for sub_idx, chunk_text in enumerate(raw_chunks, start=1):
                chunk_counter += 1
                # Prepend metadata banner so both embeddings and Gemini know exact provenance
                contextualized_text = (
                    f"[DOCUMENT: {doc_id} | REVISION: {meta['revision']} | "
                    f"EFFECTIVE DATE: {meta['effective_date']} | STATUS: {status} | "
                    f"FILE: {meta['filename']} | PAGE: {page_num}]\n"
                    f"{chunk_text}"
                )

                all_chunks.append(
                    {
                        "chunk_id": chunk_counter,
                        "filename": meta["filename"],
                        "doc_id": doc_id,
                        "title": meta["title"],
                        "revision": meta["revision"],
                        "effective_date": meta["effective_date"],
                        "status": status,
                        "is_superseded": is_superseded,
                        "page_number": page_num,
                        "part_on_page": sub_idx,
                        "raw_text": chunk_text,
                        "contextualized_text": contextualized_text,
                    }
                )

    return all_chunks 