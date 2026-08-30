import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest

from backend.language.detector import detect_language_structured
from backend.rag.fusion import reciprocal_rank_fusion
from backend.rag.reranker import (
    BaseReranker, PassthroughReranker, SemanticLexicalReranker, 
    CrossEncoderReranker, get_reranker, rerank_candidates
)
from backend.rag.validator import validate_evidence, detect_contradictions, check_intent_coverage
from backend.rag.ingestion import calculate_file_checksum, detect_sections_and_chunk
from backend.rag.vector_store import store_chunks, vector_search
from backend.rag.engine import get_rag_engine

class TestMasterEngineeringSuite(unittest.TestCase):

    # --- 1. Provenance & Versioning Tests ---
    def test_checksum_consistency(self):
        tmp_path = "tests/test_sha.tmp"
        with open(tmp_path, "w") as f:
            f.write("Official Government Scheme v2024.1")
        
        sha1 = calculate_file_checksum(tmp_path)
        sha2 = calculate_file_checksum(tmp_path)
        self.assertEqual(sha1, sha2)
        self.assertEqual(len(sha1), 64)
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    def test_chunk_provenance_retention(self):
        pages = [{"page_num": 1, "text": "KALIA Scheme provides Rs 10000 financial support to farmers."}]
        chunks = detect_sections_and_chunk(
            pages=pages,
            doc_id="doc-kalia-99",
            doc_title="KALIA Yojana Guidelines",
            department="Agriculture & Farmers Empowerment",
            category="Scheme",
            language="en",
            version="2024.1",
            source_type="demo",
            authority_level="demo",
            source_url="https://kalia.odisha.gov.in",
            publisher="Govt of Odisha",
            publication_date="2024-01-01",
            status="active"
        )
        self.assertEqual(len(chunks), 1)
        c = chunks[0]
        self.assertEqual(c["document_id"], "doc-kalia-99")
        self.assertEqual(c["version"], "2024.1")
        self.assertEqual(c["source_type"], "demo")
        self.assertEqual(c["authority_level"], "demo")
        self.assertEqual(c["publisher"], "Govt of Odisha")
        self.assertEqual(c["status"], "active")

    # --- 2. Reranker & Fusion Tests ---
    def test_fusion_and_reranker_interface(self):
        # 1. Fusion
        vec_res = [{"chunk_id": "c1", "score": 0.9, "text": "KALIA eligibility", "authority_level": "official"}]
        bm25_res = [{"chunk_id": "c1", "bm25_score": 0.8, "text": "KALIA eligibility", "authority_level": "official"}]
        fused = reciprocal_rank_fusion(vec_res, bm25_res, top_k=2)
        self.assertEqual(len(fused), 1)
        self.assertIn("rrf_score", fused[0])

        # 2. Passthrough Reranker
        pt = PassthroughReranker()
        pt_res = pt.rerank("KALIA eligibility", fused, top_k=1)
        self.assertEqual(pt_res[0]["chunk_id"], "c1")

        # 3. Semantic Lexical Reranker
        sl = SemanticLexicalReranker()
        candidates = [
            {"chunk_id": "c_irrelevant", "score": 0.5, "text": "Random topic text", "section": "Other", "authority_level": "user_uploaded"},
            {"chunk_id": "c_relevant", "score": 0.5, "text": "KALIA eligibility criteria for resident farmers", "section": "Eligibility", "authority_level": "official"}
        ]
        sl_res = sl.rerank("KALIA eligibility criteria", candidates, top_k=2)
        self.assertEqual(sl_res[0]["chunk_id"], "c_relevant")
        self.assertGreater(sl_res[0]["score"], sl_res[1]["score"])

    # --- 3. Multilingual & Mixed Detection Tests ---
    def test_language_detection_spectrum(self):
        # English
        en = detect_language_structured("What are the key benefits of BSKY health card?")
        self.assertEqual(en["language"], "en")
        self.assertEqual(en["script"], "latin")
        self.assertFalse(en["is_mixed"])

        # Hindi (Devanagari)
        hi = detect_language_structured("कालिया योजना के तहत कितनी सहायता मिलती है?")
        self.assertEqual(hi["language"], "hi")
        self.assertEqual(hi["script"], "devanagari")
        self.assertFalse(hi["is_mixed"])

        # Hinglish (Romanized Hindi)
        hinglish = detect_language_structured("KALIA yojana me apply karne ke liye kaunse dastavez chahiye?")
        self.assertEqual(hinglish["language"], "hi-en")
        self.assertEqual(hinglish["script"], "latin")
        self.assertFalse(hinglish["is_mixed"])

        # Odia (Odia script)
        odia = detect_language_structured("କାଳିଆ ଯୋଜନାରେ କଣ ସବୁ ଯୋଗ୍ୟତା ଆବଶ୍ୟକ?")
        self.assertEqual(odia["language"], "or")
        self.assertEqual(odia["script"], "odia")
        self.assertFalse(odia["is_mixed"])

        # Mixed Script (Devanagari + Latin)
        mixed = detect_language_structured("BSKY card के liye eligibility kya hai?")
        self.assertEqual(mixed["language"], "hi-en")

    # --- 4. Multi-Signal Evidence & Contradiction Tests ---
    def test_evidence_validator_levels(self):
        # Empty sources -> Insufficient
        ok, score, level, fb, conflicts = validate_evidence([], "en")
        self.assertFalse(ok)
        self.assertEqual(level, "INSUFFICIENT")
        self.assertTrue(len(fb) > 0)

        # Strong sources -> High
        strong_sources = [
            {"score": 0.85, "text": "KALIA Scheme provides Rs 10000 to small farmers with Aadhaar card.", "authority_level": "official", "section": "Eligibility"},
            {"score": 0.80, "text": "Documents needed: Aadhaar Card and Bank Passbook.", "authority_level": "official", "section": "Documents"}
        ]
        ok, score, level, fb, conflicts = validate_evidence(strong_sources, "en", query="What documents are needed for KALIA?")
        self.assertTrue(ok)
        self.assertEqual(level, "HIGH")

    def test_contradiction_detection(self):
        conflicting_sources = [
            {"document_title": "KALIA Scheme v1.0", "text": "Assistance amount is Rs 5000 per family."},
            {"document_title": "KALIA Scheme v2.0", "text": "Assistance amount is Rs 10000 per family."}
        ]
        has_conflict, details = detect_contradictions(conflicting_sources)
        self.assertTrue(has_conflict)
        self.assertTrue(len(details) > 0)

    # --- 5. End-to-End RAG Engine Pipeline ---
    def test_end_to_end_rag_answering(self):
        engine = get_rag_engine()
        
        # Ensure active KALIA test chunk is present in store
        test_chunks = [{
            "chunk_id": "test_kalia_active_c1",
            "document_id": "kalia-scheme-doc",
            "document_title": "KALIA Yojana Guidelines",
            "title": "KALIA Yojana Guidelines",
            "section": "Financial Assistance & Benefits",
            "department": "Agriculture & Farmers Empowerment",
            "language": "en",
            "version": "2024.1",
            "source_type": "official",
            "authority_level": "official",
            "source_url": "https://kalia.odisha.gov.in",
            "status": "active",
            "text": "KALIA Scheme provides financial assistance of Rs 10,000 per family per year to small and marginal farmers."
        }]
        store_chunks(test_chunks)
        
        # Test Query against KALIA Scheme
        res = engine.answer_query(
            query="What is the financial benefit under KALIA yojana?",
            preferred_language="en"
        )
        self.assertFalse(res["is_fallback"])
        self.assertGreater(len(res["sources"]), 0)
        self.assertTrue("10" in res["answer"] or "KALIA" in res["answer"] or "assistance" in res["answer"].lower())
        self.assertIn(res["evidence_level"], ["HIGH", "MEDIUM"])

        # Test Out-of-Domain Query -> Localized Fallback
        res_fb = engine.answer_query(
            query="What is the nuclear physics syllabus at Stanford University?",
            preferred_language="hi"
        )
        self.assertTrue(res_fb["is_fallback"])
        self.assertEqual(len(res_fb["sources"]), 0)

if __name__ == "__main__":
    unittest.main()
