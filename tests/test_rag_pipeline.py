import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from backend.language.detector import detect_language_structured, detect_language
from backend.language.normalizer import normalize_text, tokenize_multilingual
from backend.rag.bm25 import MultilingualBM25Index
from backend.rag.fusion import reciprocal_rank_fusion
from backend.rag.query_processor import process_and_rewrite_query
from backend.rag.validator import validate_evidence
from backend.rag.prompts import build_generation_prompt, FALLBACK_MESSAGES

def test_language_detection_english():
    res = detect_language_structured("What documents are required for the scholarship?")
    assert res["language"] == "en"
    assert res["script"] == "latin"
    assert res["display_name"] == "ENGLISH"

def test_language_detection_hindi():
    res = detect_language_structured("इस योजना के लिए कौन से दस्तावेज़ चाहिए?")
    assert res["language"] == "hi"
    assert res["script"] == "devanagari"
    assert res["display_name"] == "HINDI"

def test_language_detection_hinglish():
    res = detect_language_structured("KALIA yojana me kitna paisa milega?")
    assert res["language"] == "hi-en"
    assert res["script"] == "latin"
    assert res["display_name"] == "HINGLISH"

def test_language_detection_odia():
    res = detect_language_structured("କାଳିଆ ଯୋଜନାରେ କେତେ ଟଙ୍କା ମିଳିବ?")
    assert res["language"] == "or"
    assert res["script"] == "odia"
    assert res["display_name"] == "ODIA"

def test_multilingual_bm25():
    idx = MultilingualBM25Index()
    docs = [
        {"chunk_id": "c1", "text": "KALIA Scheme provides Rs 10000 to small farmers.", "language": "en"},
        {"chunk_id": "c2", "text": "BSKY card provides cashless treatment up to Rs 5 Lakh.", "language": "en"},
        {"chunk_id": "c3", "text": "Madhu Babu Pension provides monthly financial assistance.", "language": "en"}
    ]
    idx.index_documents(docs)
    
    hits = idx.search("farmers assistance KALIA", top_k=2)
    assert len(hits) > 0
    assert hits[0]["chunk_id"] == "c1"

def test_reciprocal_rank_fusion():
    vec_results = [
        {"chunk_id": "doc1", "score": 0.9, "text": "Vector match 1"},
        {"chunk_id": "doc2", "score": 0.8, "text": "Vector match 2"}
    ]
    bm25_results = [
        {"chunk_id": "doc2", "bm25_score": 0.95, "text": "BM25 match 2"},
        {"chunk_id": "doc3", "bm25_score": 0.7, "text": "BM25 match 3"}
    ]
    fused = reciprocal_rank_fusion(vec_results, bm25_results, top_k=2)
    assert len(fused) == 2
    # doc2 appeared in both so should rank higher or equal
    assert "score" in fused[0]
    assert "rrf_score" in fused[0]

def test_conversational_query_rewriting():
    history = [
        {"role": "user", "content": "Tell me about KALIA Yojana"},
        {"role": "assistant", "content": "KALIA Yojana is an official scheme for farmers in Odisha."}
    ]
    res = process_and_rewrite_query("What are the eligibility criteria?", conversation_history=history)
    assert res["is_follow_up"] is True
    assert "KALIA" in res["search_query"]

def test_evidence_validator_fallback():
    # Empty sources
    is_valid, conf, level, fb, conflicts = validate_evidence([], "en")
    assert is_valid is False
    assert level == "INSUFFICIENT"
    assert "reliable information" in fb

    # Low score
    low_sources = [{"score": 0.1, "text": "Unrelated text"}]
    is_valid, conf, level, fb, conflicts = validate_evidence(low_sources, "hi-en")
    assert is_valid is False
    assert "reliable information" in fb or "knowledge base" in fb

def test_evidence_validator_success():
    high_sources = [
        {"score": 0.85, "text": "KALIA Yojana eligibility and resident criteria", "authority_level": "official", "section": "Eligibility"},
        {"score": 0.80, "text": "Small and marginal farmers of Odisha", "authority_level": "official", "section": "Eligibility"}
    ]
    is_valid, conf, level, fb, conflicts = validate_evidence(high_sources, "en")
    assert is_valid is True
    assert conf >= 0.70
    assert fb == ""

if __name__ == "__main__":
    test_language_detection_english()
    test_language_detection_hindi()
    test_language_detection_hinglish()
    test_language_detection_odia()
    test_multilingual_bm25()
    test_reciprocal_rank_fusion()
    test_conversational_query_rewriting()
    test_evidence_validator_fallback()
    test_evidence_validator_success()
    print("All tests passed in test_rag_pipeline.py!")
