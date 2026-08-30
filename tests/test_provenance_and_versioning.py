import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import unittest
from backend.models.database import SessionLocal, DocumentMetadata, User
from backend.rag.ingestion import calculate_file_checksum, detect_sections_and_chunk
from backend.rag.vector_store import store_chunks, archive_document_chunks, vector_search, get_chroma_client

class TestProvenanceAndVersioning(unittest.TestCase):
    def test_checksum_calculation(self):
        test_file = "tests/test_checksum.tmp"
        with open(test_file, "w") as f:
            f.write("Test content for checksum validation")
        
        c1 = calculate_file_checksum(test_file)
        c2 = calculate_file_checksum(test_file)
        self.assertEqual(c1, c2)
        self.assertEqual(len(c1), 64) # SHA-256 length
        if os.path.exists(test_file):
            os.remove(test_file)

    def test_provenance_metadata_attachment(self):
        pages = [{"page_num": 1, "text": "Eligibility: Resident of Odisha. Benefits: Rs 10000 assistance."}]
        chunks = detect_sections_and_chunk(
            pages=pages,
            doc_id="test-doc-123",
            doc_title="KALIA Scheme",
            department="Agriculture",
            category="Scheme",
            language="en",
            version="2024.1",
            source_type="official",
            authority_level="official",
            source_url="https://kalia.odisha.gov.in",
            status="active"
        )
        
        self.assertGreater(len(chunks), 0)
        chunk = chunks[0]
        self.assertEqual(chunk["document_id"], "test-doc-123")
        self.assertEqual(chunk["version"], "2024.1")
        self.assertEqual(chunk["source_type"], "official")
        self.assertEqual(chunk["authority_level"], "official")
        self.assertEqual(chunk["source_url"], "https://kalia.odisha.gov.in")
        self.assertEqual(chunk["status"], "active")

    def test_archived_document_exclusion(self):
        # Index an active chunk and an archived chunk
        chunks = [
            {
                "chunk_id": "kalia_v1_c1",
                "document_id": "kalia_v1",
                "document_title": "KALIA Scheme v1",
                "title": "KALIA Scheme v1",
                "section": "Eligibility",
                "department": "Agriculture",
                "version": "1.0",
                "source_type": "official",
                "authority_level": "official",
                "status": "archived",
                "text": "KALIA Scheme v1 grants old rate Rs 5000."
            },
            {
                "chunk_id": "kalia_v2_c1",
                "document_id": "kalia_v2",
                "document_title": "KALIA Scheme v2",
                "title": "KALIA Scheme v2",
                "section": "Eligibility",
                "department": "Agriculture",
                "version": "2.0",
                "source_type": "official",
                "authority_level": "official",
                "status": "active",
                "text": "KALIA Scheme v2 grants updated rate Rs 10000."
            }
        ]
        store_chunks(chunks)
        
        # Test vector search with only_active=True
        results = vector_search("KALIA Scheme rate", top_k=5, only_active=True)
        retrieved_ids = [r.get("chunk_id") for r in results]
        self.assertIn("kalia_v2_c1", retrieved_ids)
        self.assertNotIn("kalia_v1_c1", retrieved_ids)

if __name__ == "__main__":
    unittest.main()
