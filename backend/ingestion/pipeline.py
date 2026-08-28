import os
import fitz  # PyMuPDF
from backend.config import get_settings
from backend.models.database import DocumentMetadata, SessionLocal
from backend.retrieval.retriever import get_chroma_client, get_embedder

settings = get_settings()

def extract_text_from_pdf(file_path: str) -> list[dict]:
    pages = []
    doc = fitz.open(file_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append({"text": text, "page_num": page_num + 1})
    doc.close()
    return pages

def chunk_text(pages: list[dict], chunk_size=512, overlap=50) -> list[dict]:
    chunks = []
    for page in pages:
        text = page["text"]
        words = text.split()
        for i in range(0, max(1, len(words)), max(1, chunk_size - overlap)):
            chunk_words = words[i:i + chunk_size]
            chunk_text_str = " ".join(chunk_words)
            if chunk_text_str.strip():
                chunks.append({
                    "text": chunk_text_str,
                    "page": page["page_num"],
                    "chunk_index": len(chunks)
                })
    if not chunks and pages:
        for idx, page in enumerate(pages):
            chunks.append({
                "text": page["text"],
                "page": page["page_num"],
                "chunk_index": idx
            })
    return chunks

def embed_and_store(chunks: list[dict], doc_metadata: dict, collection_name='documents'):
    chroma_client = get_chroma_client()
    embedder = get_embedder()
    collection = chroma_client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )
    
    texts = [c["text"] for c in chunks]
    embeddings = embedder.encode(texts, normalize_embeddings=True).tolist()
    
    ids = [f"{doc_metadata['document_id']}_chunk_{c['chunk_index']}" for c in chunks]
    metadatas = [
        {
            "source": doc_metadata["source"],
            "page": c["page"],
            "department": doc_metadata["department"],
            "language": doc_metadata["language"],
            "version": doc_metadata["version"],
            "document_id": doc_metadata["document_id"]
        } for c in chunks
    ]
    
    collection.add(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

def run_ingestion_pipeline(file_path: str, doc_id: str, department: str, language: str, version: str):
    db = SessionLocal()
    try:
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if not doc:
            return
            
        doc.status = 'extracting'
        db.commit()
        
        pages = extract_text_from_pdf(file_path)
        
        doc.status = 'chunking'
        db.commit()
        
        chunks = chunk_text(pages)
        
        doc.status = 'embedding'
        db.commit()
        
        meta = {
            "source": doc.filename,
            "department": department,
            "language": language,
            "version": version,
            "document_id": doc_id
        }
        
        embed_and_store(chunks, meta)
        
        doc.status = 'pending_approval'
        db.commit()
    except Exception as e:
        print(f"Ingestion failed: {e}")
        doc = db.query(DocumentMetadata).filter(DocumentMetadata.id == doc_id).first()
        if doc:
            doc.status = 'failed'
            db.commit()
    finally:
        db.close()
