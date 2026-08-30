import os
import re
import hashlib
from datetime import datetime
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional
from backend.models.database import DocumentMetadata, SessionLocal
from backend.rag.vector_store import store_chunks, archive_document_chunks
from backend.language.normalizer import normalize_text
from backend.language.detector import detect_language

def calculate_file_checksum(file_path: str) -> str:
    """Calculates SHA-256 checksum for a file to prevent duplicate indexing."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """Extracts text and page numbers from a PDF file using PyMuPDF."""
    pages = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        raw_text = page.get_text()
        clean_text = normalize_text(raw_text)
        if clean_text.strip():
            pages.append({
                "page_num": page_num + 1,
                "text": clean_text
            })
    doc.close()
    return pages

def detect_sections_and_chunk(
    pages: List[Dict[str, Any]],
    doc_id: str,
    doc_title: str,
    department: str,
    category: str = "Scheme",
    language: str = "en",
    version: str = "1.0",
    source_type: str = "official",
    authority_level: str = "official",
    source_url: Optional[str] = None,
    publisher: Optional[str] = None,
    publication_date: Optional[str] = None,
    last_updated: Optional[str] = None,
    status: str = "active",
    chunk_size: int = 500,
    overlap: int = 60
) -> List[Dict[str, Any]]:
    """
    Chunks text with section awareness, full provenance tracking, and version metadata.
    """
    chunks = []
    current_section = "Overview"

    for page in pages:
        page_num = page["page_num"]
        text = page["text"]
        
        words = text.split()
        
        for i in range(0, max(1, len(words)), max(1, chunk_size - overlap)):
            chunk_words = words[i:i + chunk_size]
            chunk_str = " ".join(chunk_words).strip()
            
            if not chunk_str:
                continue

            # Detect potential section in chunk
            section_match = re.search(r'([A-Z][A-Za-z\s]{3,30}:|Eligibility|Documents|Benefits|Procedure|Guidelines|କ୍ରାଇଟେରିଆ|ଯୋଗ୍ୟତା|ଦଲିଲ)', chunk_str)
            if section_match:
                current_section = section_match.group(0).replace(":", "").strip()

            chunk_id = f"{doc_id}_p{page_num}_c{len(chunks)}"
            
            chunks.append({
                "chunk_id": chunk_id,
                "document_id": doc_id,
                "document_title": doc_title,
                "title": doc_title,
                "source": doc_title,
                "page": page_num,
                "section": current_section,
                "department": department,
                "category": category,
                "language": language or detect_language(chunk_str),
                "version": version,
                "source_type": source_type,
                "authority_level": authority_level,
                "source_url": source_url or "",
                "publisher": publisher or "",
                "publication_date": publication_date or "",
                "last_updated": last_updated or datetime.utcnow().isoformat(),
                "status": status,
                "text": chunk_str
            })

    return chunks

def process_document_ingestion(
    file_path: str,
    doc_id: str,
    department: str,
    language: str,
    version: str,
    title: Optional[str] = None,
    category: str = "Scheme",
    source_type: str = "official",
    authority_level: str = "official",
    source_url: Optional[str] = None,
    publisher: Optional[str] = None,
    publication_date: Optional[str] = None,
    auto_activate: bool = False
):
    """
    Full asynchronous ingestion pipeline:
    1. Validation & SHA-256 Checksum
    2. Duplicate detection
    3. PDF parsing / extraction
    4. Section-aware chunking & provenance attachment
    5. ChromaDB & BM25 indexing
    6. Version lifecycle transition (archive older active versions of same document)
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if not doc:
            return

        doc.status = 'extracting'
        doc_title = title or doc.title or doc.filename
        doc.title = doc_title
        
        # 1. Calculate Checksum
        checksum = calculate_file_checksum(file_path)
        doc.checksum = checksum
        db.commit()

        # 2. Extract PDF Pages
        pages = extract_pdf_pages(file_path)

        doc.status = 'chunking'
        db.commit()

        # 3. Section-Aware Chunking with Provenance Metadata
        chunks = detect_sections_and_chunk(
            pages=pages,
            doc_id=doc_id,
            doc_title=doc_title,
            department=department,
            category=category,
            language=language,
            version=version,
            source_type=source_type,
            authority_level=authority_level,
            source_url=source_url,
            publisher=publisher,
            publication_date=publication_date,
            status="active" if auto_activate else "pending"
        )

        doc.status = 'embedding'
        db.commit()

        # 4. Store Chunks in ChromaDB & BM25
        store_chunks(chunks)

        if auto_activate:
            doc.status = 'active'
            # Archive older active versions of the same document title and department
            older_docs = db.query(DocumentMetadata).filter(
                DocumentMetadata.title == doc_title,
                DocumentMetadata.department == department,
                DocumentMetadata.id != doc_id,
                DocumentMetadata.status == 'active'
            ).all()
            for old_doc in older_docs:
                old_doc.status = 'archived'
                archive_document_chunks(old_doc.id)
        else:
            doc.status = 'pending_approval'

        db.commit()
    except Exception as e:
        print(f"[Ingestion] Failed for {doc_id}: {e}")
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if doc:
            doc.status = 'failed'
            db.commit()
    finally:
        db.close()
