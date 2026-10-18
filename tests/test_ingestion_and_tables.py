import os
import sys
import unittest
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.rag.ingestion import (
    format_table_as_markdown,
    extract_ocr_from_page,
    extract_pdf_pages,
    extract_text_document_pages,
    extract_csv_document_pages,
    extract_document_pages,
    detect_sections_and_chunk,
    calculate_file_checksum
)

class TestIngestionAndTableExtraction(unittest.TestCase):

    def test_format_table_as_markdown_basic(self):
        rows = [
            ["Scheme", "Amount", "Frequency"],
            ["KALIA", "Rs 10,000", "2 Installments"],
            ["MBPY", "Rs 1,000", "Monthly"]
        ]
        md = format_table_as_markdown(rows)
        self.assertIn("| Scheme | Amount | Frequency |", md)
        self.assertIn("| --- | --- | --- |", md)
        self.assertIn("| KALIA | Rs 10,000 | 2 Installments |", md)
        self.assertIn("| MBPY | Rs 1,000 | Monthly |", md)

    def test_format_table_as_markdown_escaping(self):
        rows = [
            ["Header | Note", "Details"],
            ["Value | 1", "Active"]
        ]
        md = format_table_as_markdown(rows)
        self.assertIn("Header \\| Note", md)
        self.assertIn("Value \\| 1", md)

    def test_format_table_empty_handling(self):
        self.assertEqual(format_table_as_markdown([]), "")
        self.assertEqual(format_table_as_markdown([["Header Only"]]), "")
        self.assertEqual(format_table_as_markdown("invalid"), "")

    def test_extract_text_and_markdown_document_pages(self):
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False) as f:
            f.write("# Scheme Overview\n\nOfficial guidelines for citizen welfare.\n\n---\n\n## Eligibility\n\n| Level | Criteria |\n|---|---|\n| Full | Resident |")
            tmp_name = f.name

        try:
            pages = extract_text_document_pages(tmp_name)
            self.assertEqual(len(pages), 2)
            self.assertEqual(pages[0]["page_num"], 1)
            self.assertFalse(pages[0]["has_tables"])
            self.assertEqual(pages[1]["page_num"], 2)
            self.assertTrue(pages[1]["has_tables"])
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_extract_csv_document_pages(self):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as f:
            f.write("Scheme,Coverage,Department\nBSKY,500000,Health\nKALIA,10000,Agriculture\n")
            tmp_name = f.name

        try:
            pages = extract_csv_document_pages(tmp_name)
            self.assertEqual(len(pages), 1)
            self.assertTrue(pages[0]["has_tables"])
            self.assertIn("| Scheme | Coverage | Department |", pages[0]["text"])
            self.assertIn("BSKY", pages[0]["text"])
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_extract_document_pages_dispatcher(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("Plain text policy guideline document.")
            tmp_name = f.name

        try:
            pages = extract_document_pages(tmp_name)
            self.assertEqual(len(pages), 1)
            self.assertIn("Plain text policy guideline document", pages[0]["text"])
        finally:
            if os.path.exists(tmp_name):
                os.remove(tmp_name)

    def test_multilingual_section_detection(self):
        # English section
        en_pages = [{"page_num": 1, "text": "Financial Assistance: Small and Marginal Farmers receive Rs 10000."}]
        en_chunks = detect_sections_and_chunk(en_pages, "doc-en", "KALIA", "Agriculture")
        self.assertEqual(en_chunks[0]["section"], "Financial Assistance")

        # Hindi (Devanagari) section
        hi_pages = [{"page_num": 1, "text": "पात्रता: ओडिशा के किसान इस योजना के पात्र हैं।"}]
        hi_chunks = detect_sections_and_chunk(hi_pages, "doc-hi", "KALIA", "Agriculture")
        self.assertEqual(hi_chunks[0]["section"], "पात्रता")

        # Odia section
        or_pages = [{"page_num": 1, "text": "ଯୋଗ୍ୟତା: ଓଡ଼ିଶାର ଚାଷୀମାନେ ଏହି ଯୋଜନାର ଲାଭ ପାଇବେ।"}]
        or_chunks = detect_sections_and_chunk(or_pages, "doc-or", "KALIA", "Agriculture")
        self.assertEqual(or_chunks[0]["section"], "ଯୋଗ୍ୟତା")

    def test_seed_pdfs_table_extraction(self):
        seed_dir = os.path.join(os.path.dirname(__file__), "..", "backend", "seed_documents")
        kalia_pdf = os.path.join(seed_dir, "kalia_yojana_guidelines.pdf")
        if os.path.exists(kalia_pdf):
            pages = extract_pdf_pages(kalia_pdf)
            self.assertGreater(len(pages), 0)
            self.assertTrue(any(p.get("has_tables", False) for p in pages))
            # Verify table markdown presence in extracted text
            kalia_text = " ".join(p["text"] for p in pages)
            self.assertIn("Extracted Tables", kalia_text)
            self.assertIn("Small & Marginal Farmers", kalia_text)

if __name__ == "__main__":
    unittest.main()
