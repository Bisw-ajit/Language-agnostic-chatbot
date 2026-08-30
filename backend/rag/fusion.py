from typing import List, Dict, Any

def reciprocal_rank_fusion(
    vector_results: List[Dict[str, Any]],
    bm25_results: List[Dict[str, Any]],
    rrf_k: int = 60,
    vector_weight: float = 0.65,
    bm25_weight: float = 0.35,
    top_k: int = 5
) -> List[Dict[str, Any]]:
    """
    Fuses Vector Search and BM25 Search rankings using Reciprocal Rank Fusion (RRF).
    """
    scores: Dict[str, float] = {}
    doc_map: Dict[str, Dict[str, Any]] = {}

    # Process Vector Results
    for rank, doc in enumerate(vector_results):
        chunk_id = doc.get("chunk_id") or doc.get("document_id", "") + "_" + str(doc.get("page", 1))
        rrf_val = vector_weight * (1.0 / (rrf_k + rank + 1))
        scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_val
        
        if chunk_id not in doc_map:
            doc_map[chunk_id] = dict(doc)
        doc_map[chunk_id]["vector_rank"] = rank + 1
        doc_map[chunk_id]["vector_score"] = doc.get("vector_score", doc.get("score", 0.0))

    # Process BM25 Results
    for rank, doc in enumerate(bm25_results):
        chunk_id = doc.get("chunk_id") or doc.get("document_id", "") + "_" + str(doc.get("page", 1))
        rrf_val = bm25_weight * (1.0 / (rrf_k + rank + 1))
        scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_val
        
        if chunk_id not in doc_map:
            doc_map[chunk_id] = dict(doc)
        doc_map[chunk_id]["bm25_rank"] = rank + 1
        doc_map[chunk_id]["bm25_score"] = doc.get("bm25_score", 0.0)

    # Sort merged candidates by RRF score
    sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)

    fused_results: List[Dict[str, Any]] = []
    max_rrf = max(scores.values()) if scores else 1.0

    for cid in sorted_chunk_ids[:top_k]:
        doc = doc_map[cid]
        # Calculate a unified confidence score (blend of vector similarity & BM25 normalized score)
        v_score = doc.get("vector_score", 0.0)
        b_score = doc.get("bm25_score", 0.0)
        
        # Primary confidence reflects semantic similarity with lexical reinforcement
        if v_score > 0 and b_score > 0:
            unified_score = round(min(1.0, 0.7 * v_score + 0.3 * b_score + 0.05), 3)
        elif v_score > 0:
            unified_score = round(v_score, 3)
        else:
            unified_score = round(min(1.0, b_score * 0.8), 3)

        doc["rrf_score"] = round(scores[cid] / max(1e-6, max_rrf), 3)
        doc["score"] = unified_score
        
        if "excerpt" not in doc:
            txt = doc.get("text", "")
            doc["excerpt"] = txt[:220] + "..." if len(txt) > 220 else txt

        fused_results.append(doc)

    return fused_results
