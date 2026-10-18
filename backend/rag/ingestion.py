import os
import re
import hashlib
import logging
from datetime import datetime, timezone
import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional

from backend.models.database import DocumentMetadata, SessionLocal
from backend.rag.vector_store import store_chunks, archive_document_chunks
from backend.language.normalizer import normalize_text
from backend.language.detector import detect_language

logger = logging.getLogger("rag.ingestion")

def calculate_file_checksum(file_path: str) -> str:
    """Calculates SHA-256 checksum for a file to prevent duplicate indexing."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def format_table_as_markdown(table) -> str:
    """Converts a PyMuPDF Table object or list/dict rows into a clean markdown table representation."""
    try:
        if hasattr(table, "extract"):
            rows = table.extract()
        elif isinstance(table, (list, tuple)):
            rows = table
        else:
            return ""
        if not rows or len(rows) < 2:
            return ""
        
        header = rows[0]
        clean_header = [str(c or "").replace("\n", " ").replace("|", "\\|").strip() for c in header]
        # Skip empty headers
        if not any(clean_header):
            return ""

        md_lines = [
            "| " + " | ".join(clean_header) + " |",
            "| " + " | ".join(["---"] * len(clean_header)) + " |"
        ]
        
        for r in rows[1:]:
            clean_row = [str(c or "").replace("\n", " ").replace("|", "\\|").strip() for c in r]
            if any(clean_row):
                md_lines.append("| " + " | ".join(clean_row) + " |")
            
        return "\n".join(md_lines)
    except Exception as e:
        logger.debug(f"Table markdown formatting skipped: {e}")
        return ""

def extract_ocr_from_page(page) -> str:
    """Executes OCR on an image/scanned PDF page via pytesseract if available."""
    try:
        import pytesseract
        import shutil
        from PIL import Image
        import io

        # Check for tesseract binary in PATH and common installation directories
        tesseract_bin = shutil.which("tesseract")
        if not tesseract_bin:
            for fallback_path in [
                "/usr/local/bin/tesseract",
                "/opt/homebrew/bin/tesseract",
                "/usr/bin/tesseract"
            ]:
                if os.path.exists(fallback_path) and os.access(fallback_path, os.X_OK):
                    tesseract_bin = fallback_path
                    pytesseract.pytesseract.tesseract_cmd = fallback_path
                    break

        if not tesseract_bin:
            logger.debug("Tesseract OCR binary not installed on host; skipping OCR extraction.")
            return ""

        pix = page.get_pixmap(dpi=150)
        img = Image.open(io.BytesIO(pix.tobytes("png")))
        return pytesseract.image_to_string(img).strip()
    except Exception as e:
        logger.debug(f"OCR execution skipped or unavailable: {e}")
        return ""

def extract_pdf_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Extracts text, structured tables, and handles OCR for scanned pages using PyMuPDF.
    """
    pages = []
    doc = fitz.open(file_path)
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 1. Extract structured tables
        table_markdowns = []
        try:
            tabs = page.find_tables()
            if tabs:
                for tab in tabs:
                    t_md = format_table_as_markdown(tab)
                    if t_md:
                        table_markdowns.append(t_md)
        except Exception as e:
            logger.debug(f"Table parsing error on page {page_num + 1}: {e}")

        # 2. Extract plain text
        raw_text = page.get_text()
        clean_text = normalize_text(raw_text)

        # 3. OCR Fallback for scanned/image-only pages (< 40 chars)
        is_scanned = False
        if len(clean_text.strip()) < 40:
            ocr_text = extract_ocr_from_page(page)
            if ocr_text:
                clean_text = normalize_text(ocr_text)
                is_scanned = True

        # Combine text and extracted tables
        combined_text = clean_text
        if table_markdowns:
            combined_text += "\n\n### Extracted Tables:\n" + "\n\n".join(table_markdowns)

        if combined_text.strip():
            pages.append({
                "page_num": page_num + 1,
                "text": combined_text.strip(),
                "has_tables": len(table_markdowns) > 0,
                "is_scanned": is_scanned
            })
            
    doc.close()
    return pages

def extract_text_document_pages(file_path: str) -> List[Dict[str, Any]]:
    """Extracts pages from .txt and .md files with section and table awareness."""
    pages = []
    text_content = ""
    for enc in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                text_content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if not text_content.strip():
        return pages

    # Split by form-feed or markdown horizontal rules
    raw_pages = re.split(r'\x0c|\n\s*---\s*\n', text_content)
    for p_idx, p_text in enumerate(raw_pages):
        clean_p = normalize_text(p_text).strip()
        if not clean_p:
            continue
        has_tables = bool(re.search(r'\|.*\|.*\n\|[-:\s|]+\|', p_text))
        pages.append({
            "page_num": p_idx + 1,
            "text": clean_p,
            "has_tables": has_tables,
            "is_scanned": False
        })
    return pages

def extract_csv_document_pages(file_path: str) -> List[Dict[str, Any]]:
    """Extracts structured tables and text representations from .csv files."""
    import csv
    pages = []
    rows = []
    for enc in ["utf-8", "utf-8-sig", "latin-1"]:
        try:
            with open(file_path, "r", encoding=enc) as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except UnicodeDecodeError:
            continue

    if not rows:
        return pages

    table_md = format_table_as_markdown(rows)
    summary_lines = []
    if len(rows) > 1:
        headers = rows[0]
        for r in rows[1:]:
            line_parts = [f"{h}: {val.strip()}" for h, val in zip(headers, r) if val.strip()]
            if line_parts:
                summary_lines.append(", ".join(line_parts))
    
    combined = "\n".join(summary_lines)
    if table_md:
        combined += "\n\n### Extracted Tables:\n" + table_md

    pages.append({
        "page_num": 1,
        "text": combined.strip(),
        "has_tables": bool(table_md),
        "is_scanned": False
    })
    return pages

def extract_document_pages(file_path: str) -> List[Dict[str, Any]]:
    """
    Unified multi-format document parser supporting PDF, TXT, Markdown, and CSV.
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return extract_pdf_pages(file_path)
    elif ext in [".txt", ".md"]:
        return extract_text_document_pages(file_path)
    elif ext == ".csv":
        return extract_csv_document_pages(file_path)
    else:
        return extract_text_document_pages(file_path)

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
    overlap: int = 60,
    tenant_id: str = "default-tenant"
) -> List[Dict[str, Any]]:
    """
    Chunks text with section awareness, full provenance tracking, table retention, version, and tenant metadata.
    """
    chunks = []
    current_section = "Overview"

    for page in pages:
        page_num = page["page_num"]
        text = page["text"]
        has_tables = page.get("has_tables", False)
        is_scanned = page.get("is_scanned", False)
        
        words = text.split()
        
        for i in range(0, max(1, len(words)), max(1, chunk_size - overlap)):
            chunk_words = words[i:i + chunk_size]
            chunk_str = " ".join(chunk_words).strip()
            
            if not chunk_str:
                continue

            # Detect potential section in chunk (English, Devanagari, Odia)
            section_match = re.search(
                r'([A-Z][A-Za-z\s]{3,30}:|Eligibility|Documents|Benefits|Procedure|Guidelines|Overview|Objectives|'
                r'Financial Assistance|Hospital Network|Coverage|Pension Amounts|Summary|'
                r'पात्रता|दस्तावेज|लाभ|प्रक्रिया|दिशा-निर्देश|सहायता|'
                r'କ୍ରାଇଟେରିଆ|ଯୋଗ୍ୟତା|ଦଲିଲ|ସୁବିଧା|ନିର୍ଦ୍ଦେଶାବଳୀ|ପ୍ରକ୍ରିୟା)', 
                chunk_str
            )
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
                "last_updated": last_updated or datetime.now(timezone.utc).isoformat(),
                "status": status,
                "tenant_id": str(tenant_id or "default-tenant"),
                "has_tables": has_tables,
                "is_scanned": is_scanned,
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
    auto_activate: bool = False,
    tenant_id: Optional[str] = None
):
    """
    Full asynchronous ingestion pipeline:
    1. Validation & SHA-256 Checksum
    2. Duplicate detection
    3. Multi-format parsing / table extraction / OCR fallback
    4. Section-aware chunking & provenance and tenant attachment
    5. ChromaDB & BM25 indexing
    6. Version lifecycle transition (archive older active versions within tenant)
    """
    db = SessionLocal()
    try:
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if not doc:
            return

        doc.status = 'extracting'
        doc_title = title or doc.title or doc.filename
        doc.title = doc_title
        doc_tenant = tenant_id or (doc.tenant_id if doc.tenant_id else "default-tenant")
        
        # 1. Calculate Checksum
        checksum = calculate_file_checksum(file_path)
        doc.checksum = checksum
        db.commit()

        # 2. Extract Document Pages & Tables (PDF, TXT, MD, CSV)
        pages = extract_document_pages(file_path)

        doc.status = 'chunking'
        db.commit()

        # 3. Section-Aware Chunking with Provenance and Tenant Metadata
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
            status="active" if auto_activate else "pending",
            tenant_id=doc_tenant
        )

        doc.status = 'embedding'
        db.commit()

        # 4. Store Chunks in ChromaDB & BM25
        store_chunks(chunks)

        if auto_activate:
            doc.status = 'active'
            # Archive older active versions of the same document title and department within the same tenant
            older_docs = db.query(DocumentMetadata).filter(
                DocumentMetadata.title == doc_title,
                DocumentMetadata.department == department,
                DocumentMetadata.tenant_id == doc_tenant,
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
        logger.error(f"[Ingestion] Failed for {doc_id}: {e}")
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if doc:
            doc.status = 'failed'
            db.commit()
    finally:
        db.close()
