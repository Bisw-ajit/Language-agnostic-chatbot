import os
os.environ["HF_HUB_DISABLE_SYMLINKS_WARNING"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"
os.environ["HF_HUB_OFFLINE"] = "1"
from functools import lru_cache
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from backend.config import get_settings
from backend.rag.bm25 import get_bm25_index

settings = get_settings()

@lru_cache()
def get_chroma_client():
    os.makedirs(settings.chroma_persist_dir, exist_ok=True)
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)

_cached_embedder = None
_embedder_load_failed = False

def get_embedder():
    global _cached_embedder, _embedder_load_failed
    if _cached_embedder is not None:
        return _cached_embedder
    if _embedder_load_failed:
        return None
    try:
        _cached_embedder = SentenceTransformer(settings.embedding_model)
        return _cached_embedder
    except Exception as e:
        print(f"[VectorStore] SentenceTransformer offline/unavailable: {e}")
        _embedder_load_failed = True
        return None

def get_or_create_collection(collection_name: str = "documents"):
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=collection_name,
        metadata={"hnsw:space": "cosine"}
    )

def store_chunks(chunks: List[Dict[str, Any]], collection_name: str = "documents"):
    """
    Stores document chunks in ChromaDB with rich metadata.
    """
    if not chunks:
        return

    collection = get_or_create_collection(collection_name)
    embedder = get_embedder()

    texts = [c["text"] for c in chunks]
    ids = [c["chunk_id"] for c in chunks]
    metadatas = [
        {
            "document_id": str(c.get("document_id", "")),
            "chunk_id": str(c.get("chunk_id", "")),
            "document_title": str(c.get("document_title", c.get("title", c.get("source", "Document")))),
            "title": str(c.get("title", c.get("document_title", "Document"))),
            "source": str(c.get("source", "")),
            "page": int(c.get("page", 1)),
            "section": str(c.get("section", "General")),
            "department": str(c.get("department", "General")),
            "category": str(c.get("category", "Scheme")),
            "language": str(c.get("language", "en")),
            "version": str(c.get("version", "1.0")),
            "source_type": str(c.get("source_type", "official")),
            "authority_level": str(c.get("authority_level", "official")),
            "source_url": str(c.get("source_url", "")),
            "publisher": str(c.get("publisher", "")),
            "publication_date": str(c.get("publication_date", "")),
            "last_updated": str(c.get("last_updated", "")),
            "status": str(c.get("status", "active"))
        }
        for c in chunks
    ]

    embeddings = None
    if embedder is not None:
        try:
            embeddings = embedder.encode(texts, normalize_embeddings=True).tolist()
        except Exception as e:
            print(f"[VectorStore] Embedding encode failed: {e}")
            embeddings = None

    if embeddings is None:
        # Provide float vector to avoid Chroma invoking default network-dependent embedding function
        embeddings = [[0.0] * 384 for _ in texts]

    collection.upsert(
        documents=texts,
        embeddings=embeddings,
        metadatas=metadatas,
        ids=ids
    )

    # Refresh BM25 index with all active documents from Chroma
    sync_bm25_from_chroma(collection_name)

def archive_document_chunks(document_id: str, collection_name: str = "documents"):
    """
    Marks all chunks belonging to a document ID as 'archived' so they no longer
    participate in active BM25 or vector retrieval.
    """
    try:
        collection = get_or_create_collection(collection_name)
        data = collection.get(where={"document_id": document_id}, include=["metadatas"])
        if data and data.get("ids"):
            updated_metas = []
            for meta in data["metadatas"]:
                m = dict(meta) if meta else {}
                m["status"] = "archived"
                updated_metas.append(m)
            collection.update(ids=data["ids"], metadatas=updated_metas)
            sync_bm25_from_chroma(collection_name)
    except Exception as e:
        print(f"[VectorStore] Error archiving document {document_id}: {e}")

def delete_document_chunks(document_id: str, collection_name: str = "documents"):
    """Deletes all chunks for a document ID from Chroma and updates BM25."""
    try:
        collection = get_or_create_collection(collection_name)
        collection.delete(where={"document_id": document_id})
        sync_bm25_from_chroma(collection_name)
    except Exception as e:
        print(f"[VectorStore] Error deleting document {document_id}: {e}")

def sync_bm25_from_chroma(collection_name: str = "documents"):
    """Loads all active records from Chroma collection and updates BM25 index."""
    try:
        collection = get_or_create_collection(collection_name)
        data = collection.get(include=["documents", "metadatas"])
        
        active_docs = []
        if data and data.get("documents"):
            for text, meta in zip(data["documents"], data["metadatas"]):
                doc_item = dict(meta) if meta else {}
                # Only active chunks participate in BM25 index
                if doc_item.get("status", "active") == "active":
                    doc_item["text"] = text
                    active_docs.append(doc_item)
                
        bm25_index = get_bm25_index()
        bm25_index.build_index(active_docs)
    except Exception as e:
        print(f"[VectorStore] Error synchronizing BM25 from Chroma: {e}")

def vector_search(
    query: str,
    top_k: int = 10,
    filters: Optional[Dict[str, Any]] = None,
    only_active: bool = True,
    collection_name: str = "documents"
) -> List[Dict[str, Any]]:
    """
    Performs cosine similarity vector search over ChromaDB.
    By default filters for status == 'active'.
    Returns ranked candidate document chunks with attached 'vector_score'.
    """
    try:
        collection = get_or_create_collection(collection_name)
    except Exception:
        return []

    embedder = get_embedder()
    search_filters = dict(filters) if filters else {}
    if only_active and "status" not in search_filters:
        search_filters["status"] = "active"

    if embedder is None:
        # Fallback to BM25 ranked relevance retrieval if neural embedding model is offline
        try:
            bm25_hits = get_bm25_index().search(query, top_k=top_k)
            if bm25_hits:
                offline_results = []
                for hit in bm25_hits:
                    d = dict(hit)
                    if only_active and d.get("status", "active") != "active":
                        continue
                    sim_score = d.get("bm25_score", 0.75)
                    d["vector_score"] = sim_score
                    d["score"] = sim_score
                    t = d.get("text", "")
                    d["excerpt"] = t[:220] + "..." if len(t) > 220 else t
                    offline_results.append(d)
                return offline_results
        except Exception as e:
            print(f"[VectorStore] Offline BM25 fallback failed: {e}")
        return []

    try:
        query_embedding = embedder.encode([query], normalize_embeddings=True).tolist()
        results = collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=search_filters if search_filters else None,
            include=["documents", "metadatas", "distances"]
        )
    except Exception as e:
        print(f"[VectorStore] Vector Query failed: {e}")
        return []

    if not results['documents'] or not results['documents'][0]:
        return []

    formatted_results = []
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]

    for i in range(len(docs)):
        meta = metas[i]
        # In cosine space, dist = 1 - sim => sim = 1 - dist
        dist = distances[i]
        sim_score = max(0.0, min(1.0, 1.0 - dist))
        
        doc_dict = dict(meta)
        doc_dict["text"] = docs[i]
        doc_dict["vector_score"] = sim_score
        doc_dict["score"] = sim_score
        doc_dict["excerpt"] = docs[i][:220] + "..." if len(docs[i]) > 220 else docs[i]
        
        formatted_results.append(doc_dict)

    return formatted_results
