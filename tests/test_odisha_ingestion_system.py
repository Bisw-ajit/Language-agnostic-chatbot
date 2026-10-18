import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import csv
import pytest

from backend.rag.odisha_corpus_manager import (
    resolve_department_command,
    score_document_relevance,
    verify_official_provenance,
    clean_extracted_text,
    chunk_document_semantically,
    OdishaCorpusIngestionEngine,
    PRIORITY_REGISTRY,
    CORPUS_STATE_FILE,
    CORPUS_MANIFEST_FILE,
    REPORTS_DIR
)

def test_resolve_department_command():
    # Priority syntax
    assert resolve_department_command("PROCESS PRIORITY 1")["priority"] == "P1"
    assert resolve_department_command("PROCESS PRIORITY 2")["priority"] == "P2"
    assert resolve_department_command("P6")["priority"] == "P6"
    assert resolve_department_command("process priority 13")["priority"] == "P13"

    # Alias / name syntax
    assert resolve_department_command("PROCESS AGRICULTURE")["priority"] == "P1"
    assert resolve_department_command("process social security")["priority"] == "P2"
    assert resolve_department_command("process health")["priority"] == "P6"
    assert resolve_department_command("process msme")["priority"] == "P9"

    # Invalid
    assert resolve_department_command("PROCESS NONEXISTENT DEPT") is None

def test_score_document_relevance():
    # High relevance scheme guidelines
    score, reason = score_document_relevance(
        title="KALIA Scheme Operational Guidelines for Small Farmers",
        text_sample="Financial assistance of Rs 10000 per family for agricultural inputs and livelihood",
        department_name="Agriculture & Farmers' Empowerment",
        pdf_url="https://agri.odisha.gov.in/schemes/kalia.pdf"
    )
    assert score >= 0.75
    assert "relevant" in reason.lower()

    # Rejection of procurement / tender
    score_tender, reason_tender = score_document_relevance(
        title="Notice Inviting E-Tender for Supply of Agricultural Farm Implements",
        text_sample="Bids are invited from registered vendors for supply of tractors",
        department_name="Agriculture & Farmers' Empowerment",
        pdf_url="https://agri.odisha.gov.in/tenders/tender_implements.pdf"
    )
    assert score_tender < 0.60
    assert "rejected" in reason_tender.lower()

    # Rejection of recruitment
    score_rec, reason_rec = score_document_relevance(
        title="Walk-in-Interview Notification for Field Executives",
        text_sample="Eligible candidates may appear for walk-in interview on 15th October",
        department_name="Social Security & Empowerment of Persons with Disabilities",
        pdf_url="https://ssepd.odisha.gov.in/recruitment/walk_in.pdf"
    )
    assert score_rec < 0.60
    assert "rejected" in reason_rec.lower()

def test_verify_official_provenance():
    allowed = ["agri.odisha.gov.in", "odisha.gov.in"]
    assert verify_official_provenance("https://agri.odisha.gov.in/schemes/kalia.pdf", allowed) is True
    assert verify_official_provenance("https://sub.odisha.gov.in/doc.pdf", allowed) is True
    assert verify_official_provenance("https://foododisha.in/pds.pdf", allowed) is True
    assert verify_official_provenance("https://random-commercial-portal.com/fake.pdf", allowed) is False

def test_clean_extracted_text():
    raw = "Page 1 of 12\n\nKALIA Scheme provides Rs 10000 subsidy.\n\nDesigned & Developed by NIC\n\n- 1 -"
    cleaned = clean_extracted_text(raw)
    assert "Page 1 of 12" not in cleaned
    assert "Designed & Developed by NIC" not in cleaned
    assert "Rs 10000 subsidy" in cleaned

def test_chunk_document_semantically():
    pages = [
        {
            "page_num": 1,
            "text": "1. Overview of KALIA Scheme\nGovernment provides direct support to farmers.\n\n2. Eligibility Criteria\nFarmers with landholding below 2 hectares are eligible.",
            "has_tables": True,
            "is_scanned": False
        }
    ]
    chunks = chunk_document_semantically(
        pages=pages,
        doc_id="test_doc_001",
        doc_title="KALIA Guidelines",
        department="Agriculture & Farmers' Empowerment",
        scheme="KALIA Yojana",
        source_url="https://agri.odisha.gov.in/kalia.pdf"
    )
    assert len(chunks) > 0
    first_chunk = chunks[0]
    assert first_chunk["document_id"] == "test_doc_001"
    assert first_chunk["department"] == "Agriculture & Farmers' Empowerment"
    assert first_chunk["scheme"] == "KALIA Yojana"
    assert first_chunk["source_url"] == "https://agri.odisha.gov.in/kalia.pdf"
    assert first_chunk["status"] == "active"
    assert first_chunk["content_type"] == "text"
    assert "farmers" in first_chunk["text"].lower()
    # Verify section diversity
    sections = {c["section"] for c in chunks}
    assert len(sections) >= 1
    assert "Eligibility Criteria" in sections

def test_chunk_document_semantically_table_isolation():
    pages = [
        {
            "page_num": 1,
            "text": "1. Introduction\nFinancial assistance matrix is detailed below.",
            "tables": ["| Category | Subsidy |\n| --- | --- |\n| General | 40% |"],
            "has_tables": True,
            "is_scanned": False
        }
    ]
    chunks = chunk_document_semantically(
        pages=pages,
        doc_id="test_tbl_001",
        doc_title="Table Test Guidelines",
        department="Agriculture",
        scheme="Table Scheme",
        source_url="https://agri.odisha.gov.in/table.pdf"
    )
    table_chunks = [c for c in chunks if c["content_type"] == "table"]
    text_chunks = [c for c in chunks if c["content_type"] == "text"]
    assert len(table_chunks) == 1
    assert len(text_chunks) == 1
    assert "40%" in table_chunks[0]["text"]
    assert table_chunks[0]["has_tables"] is True

def test_rule_1_zero_synthetic_documents(tmp_path):
    """Verifies that 404 / failed downloads do NOT produce synthetic files."""
    dummy_dept = {
        "priority": "P99",
        "name": "Nonexistent Department",
        "slug": "nonexistent_dept",
        "domains": ["odisha.gov.in"],
        "primary_domain": "odisha.gov.in",
        "schemes": ["Ghost Scheme"],
        "test_queries": ["ghost query"]
    }
    engine = OdishaCorpusIngestionEngine(dummy_dept)
    # Inject a non-existent candidate document
    engine.accepted_docs = [{
        "title": "Ghost Scheme Nonexistent PDF",
        "scheme": "Ghost Scheme",
        "source_page_url": "https://odisha.gov.in/schemes",
        "pdf_url": "https://odisha.gov.in/sites/default/files/nonexistent_404_file.pdf",
        "document_type": "Scheme Guidelines",
        "relevance_score": 0.95,
        "year": "2024",
        "version": "1.0",
        "language": "en"
    }]
    engine.phase_3_download_and_verify()
    # Under Rule 1: Must NOT synthesize a PDF. Accepted docs must be 0, download failures must be 1.
    assert len(engine.accepted_docs) == 0
    assert len(engine.download_failures) == 1
    assert engine.download_failures[0]["title"] == "Ghost Scheme Nonexistent PDF"

def test_end_to_end_single_department_lifecycle(tmp_path):
    """Verifies complete Phase 1-12 lifecycle on P1."""
    dept_cfg = PRIORITY_REGISTRY["P1"]
    engine = OdishaCorpusIngestionEngine(dept_cfg)
    result = engine.execute_lifecycle()

    assert result["status"] == "completed"
    assert result["priority"] == "P1"
    assert result["documents_processed"] > 0
    assert result["total_chunks"] > 0
    assert os.path.exists(result["report_path"])

    # Verify report contents
    with open(result["report_path"], "r", encoding="utf-8") as f:
        report_text = f.read()
    assert "Department: Agriculture & Farmers' Empowerment" in report_text
    assert "PDFs discovered:" in report_text
    assert "PDFs accepted:" in report_text
    assert "Chroma vectors added:" in report_text

    # Verify corpus state JSON
    assert os.path.exists(CORPUS_STATE_FILE)
    with open(CORPUS_STATE_FILE, "r", encoding="utf-8") as f:
        state_data = json.load(f)
    assert state_data["P1"]["status"] == "completed"
    assert state_data["P1"]["documents"] > 0
    assert state_data["P1"]["chunks"] > 0

    # Verify corpus manifest CSV
    assert os.path.exists(CORPUS_MANIFEST_FILE)
    with open(CORPUS_MANIFEST_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    p1_rows = [r for r in rows if r["priority"] == "P1"]
    assert len(p1_rows) > 0
    assert all(r["sha256"] for r in p1_rows)
