import chromadb
from functools import lru_cache
from sentence_transformers import SentenceTransformer
from backend.config import get_settings

settings = get_settings()

@lru_cache()
def get_chroma_client():
    return chromadb.PersistentClient(path=settings.chroma_persist_dir)

@lru_cache()
def get_embedder():
    return SentenceTransformer(settings.embedding_model)

def retrieve(query: str, k: int = 5, filters: dict = None) -> list[dict]:
    client = get_chroma_client()
    embedder = get_embedder()
    
    try:
        collection = client.get_collection(name='documents')
    except Exception:
        return []

    query_embedding = embedder.encode([query], normalize_embeddings=True).tolist()
    
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        where=filters,
        include=["documents", "metadatas", "distances"]
    )
    
    if not results['documents'] or not results['documents'][0]:
        return []
        
    formatted_results = []
    
    docs = results['documents'][0]
    metas = results['metadatas'][0]
    distances = results['distances'][0]
    
    for i in range(len(docs)):
        meta = metas[i]
        
        # In cosine space, distance = 1 - cosine_sim, so similarity = 1 - distance
        dist = distances[i]
        score = max(0.0, min(1.0, 1.0 - dist))
        
        excerpt = docs[i][:200] + "..." if len(docs[i]) > 200 else docs[i]
        
        formatted_results.append({
            "text": docs[i],
            "source": meta.get("source", "Unknown"),
            "page": meta.get("page", 1),
            "department": meta.get("department", "Unknown"),
            "language": meta.get("language", "en"),
            "document_id": meta.get("document_id", ""),
            "score": score,
            "excerpt": excerpt
        })
        
    return formatted_results
