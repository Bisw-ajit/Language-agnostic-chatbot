# Odisha Government Corpus Ingestion Repair Report (P1–P3)
**Project**: Language Agnostic Chatbot (SIH25104)  
**Execution Timestamp**: 2026-09-22T21:22:00+05:30  
**Status**: P1–P3 Repaired, Re-indexed, and Verified | Pipeline Halted (STOP Condition Enforced)

---

## 1. Executive Summary

Following the diagnostic audit of the Odisha Government RAG Corpus Ingestion pipeline, a critical architectural defect was identified: government URLs returning HTTP 404 triggered a local fallback synthesizer (`_generate_authoritative_scheme_pdf`), resulting in artificial 1-page PDF summaries rather than authentic government source material. Furthermore, monolithic chunking (`chunk_size=450` words) and whole-page section regex matching incorrectly tagged nearly all chunks as "Overview".

In this repair cycle:
1. **RULE 1 (Zero Synthetic Documents)** was strictly implemented: `_generate_authoritative_scheme_pdf` was completely excised from `backend/rag/odisha_corpus_manager.py`. Any download failure (404, non-PDF payload, timeout) is explicitly logged as `[DOWNLOAD FAILED]` and skipped.
2. Verified live official government PDFs from `.odisha.gov.in` portals were discovered and ingested for Priorities P1, P2, and P3.
3. A block-by-block hierarchical semantic section parser was implemented, eliminating the "Overview" collapse bug.
4. Granular semantic chunking (target 100–180 words, hard bounds 40–250 words, overlap 20–30 words) was introduced with complete table isolation (`content_type="table"`).
5. All previous synthetic records were purged, and P1–P3 were re-ingested incrementally.

---

## 2. Rule 1 Enforcement: Zero Synthetic Documents

| Department | Priority | Candidate Documents | Real PDFs Verified & Downloaded | Failed Downloads (HTTP 404) | Synthetic Documents Generated |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Agriculture & Farmers' Empowerment** | P1 | 5 | 3 | 1 (*SAMRUDDHI Policy*) | **0** |
| **Social Security & Empowerment (SSEPD)** | P2 | 6 | 4 | 0 | **0** |
| **Women & Child Development / Mission Shakti** | P3 | 5 | 3 | 1 (*1989 Rules*) | **0** |
| **Total** | | **16** | **10** | **2** | **0** |

> [!IMPORTANT]
> When `Samrudhi-English_0.pdf` and `1989 rule and its amendments.pdf` returned HTTP 404, the system logged `[DOWNLOAD FAILED] HTTP failure or non-PDF payload`, recorded them in `download_failures`, and skipped them. **Zero synthetic bytes were generated.**

---

## 3. Real Official PDF Ingestion & Extraction Details

### P1: Agriculture & Farmers' Empowerment
- **Mukhyamantri Krushi Udyog Yojana (MKUY) Operational Guidelines**
  - URL: `https://agri.odisha.gov.in/sites/default/files/2021-06/MKUY_PDF.pdf`
  - File Size: 14.04 MB | SHA-256: `fd7d794e77b6...`
  - Pages: 43 | Chunks: 96 | Tables Extracted: 14 | Native Text: Rich
- **Odisha Agriculture Disaster Management Plan (DMP)**
  - URL: `https://agri.odisha.gov.in/sites/default/files/2021-06/DMP.pdf`
  - File Size: 747.1 KB | SHA-256: `a2f90307c87c...`
  - Pages: 82 | Chunks: 219 | Tables Extracted: 83 | Native Text: Rich
- **Revised Per Drop More Crop (PDMC) Operational Guidelines**
  - URL: `https://agri.odisha.gov.in/sites/default/files/2025-03/Revised%20PDMC%20Guidelinees.pdf`
  - File Size: 4.54 MB | SHA-256: `efdae89ad656...`
  - Pages: 75 | Chunks: 217 | Tables Extracted: 48 | Native Text: Rich

### P2: Social Security & Empowerment of Persons with Disabilities
- **ABADANA Scheme Operational Guidelines for Senior Citizens**
  - URL: `https://ssepd.odisha.gov.in/sites/default/files/2026-08/ABADANA%20guidelines_organized.pdf`
  - File Size: 572.6 KB | SHA-256: `424849fb72be...`
  - Pages: 23 | Chunks: 63 | Tables Extracted: 13 | Native Text: Rich
- **Odisha Rights of Persons with Disabilities Rules**
  - URL: `https://ssepd.odisha.gov.in/sites/default/files/2026-03/ORPwD%20Act%20Govt%20of%20Odisha_0.pdf`
  - File Size: 349.7 KB | SHA-256: `2aaac0a33118...`
  - Pages: 20 | Chunks: 57 | Tables Extracted: 6 | Native Text: Rich
- **National Family Benefit Scheme (NFBS) Odisha Guidelines**
  - URL: `https://ssepd.odisha.gov.in/sites/default/files/2026-07/National%20Family%20Benefit%20Scheme%20%28NFBS%29.pdf`
  - File Size: 827.4 KB | SHA-256: `4b4f192b0c36...`
  - Pages: 1 | Chunks: 1 | Tables Extracted: 0 | Native Text: Summary circular
- **Banishree Scholarship Scheme for Students with Special Needs**
  - URL: `https://ssepd.odisha.gov.in/sites/default/files/2026-08/Banishree%20-%20A%20Scheme%20of%20Scholarship%20for%20Students%20with%20Special%20Needs._1.pdf`
  - File Size: 5.77 MB | SHA-256: `a325409d73d5...`
  - Pages: 22 | Chunks: 35 | Tables Extracted: 1 | Native Text: Rich

### P3: Women & Child Development / Mission Shakti
- **Odisha State Policy for Children and Child Welfare Guidelines**
  - URL: `https://wcd.odisha.gov.in/sites/default/files/2021-06/doc20201028_152237%20%286%29.pdf`
  - File Size: 4.80 MB | SHA-256: `6ad4bc8fc5c7...`
  - Pages: 43 | Chunks: 60 | Tables Extracted: 0 | Native Text: Rich
- **Mission Shakti Selection of WSHGs for Implementation of Health Activities Guidelines**
  - URL: `https://missionshakti.odisha.gov.in/sites/default/files/2022-11/Selection%20of%20SHGs%20for%20implementation%20of%20activities%20under%20H%20%26%20FW%20Department_compressed.pdf`
  - File Size: 189.1 KB | SHA-256: `2cf524021666...`
  - Pages: 15 | Chunks: 36 | Tables Extracted: 0 | Native Text: Rich
- **Joint Guidelines for Selection of WSHGs under OSFDC Fisheries and Animal Resources**
  - URL: `https://missionshakti.odisha.gov.in/sites/default/files/2022-11/Joint%20Guidelines%20for%20SHG%20selection%20OSFDC.pdf`
  - File Size: 2.47 MB | SHA-256: `79ab79714856...`
  - Pages: 15 | Chunks: 20 | Tables Extracted: 0 | Native Text: Rich

---

## 4. Before vs After Repair Comparison

| Metric | Pre-Repair State (Audit) | Post-Repair State (Current) | Variance |
| :--- | :---: | :---: | :---: |
| **Synthetic Documents Ingested** | 15 (100% of P1–P3) | **0 (0%)** | **-100% (Completely excised)** |
| **Authentic Official Documents** | 0 | **10** | **+10 real government PDFs** |
| **Total Ingested Pages** | 15 pages | **339 pages** | **+2,160%** |
| **Total Ingested Chunks** | 25 chunks | **804 chunks** | **+3,116%** |
| **Standalone Table Chunks (`content_type="table"`)** | 0 | **165 chunks** | **+165 isolated tables** |
| **Average Words per Chunk** | 450 words | **142 words** | **Optimal RAG context window** |
| **Section Diversity** | 1 section (96% "Overview") | **7 active scheme sections** | **Full semantic hierarchy** |
| **ChromaDB Vector Total** | 36 vectors | **815 vectors** | **Production-grade corpus** |

---

## 5. Section Distribution Post-Repair

Chunks are dynamically categorized into scheme sections using block-by-block header detection:

| Section Name | Chunk Count | Coverage % | Key Content Preserved |
| :--- | :---: | :---: | :--- |
| **Overview & Objectives** | 233 | 29.0% | Preamble, vision, scheme background, target beneficiary definition |
| **Required Documents** | 212 | 26.4% | Checklists, Aadhaar / land records, UDID cards, bank passbook requirements |
| **Monitoring, Grievance & Helpdesk** | 121 | 15.0% | Nodal officers, grievance redressal, appellate authority, block offices |
| **Eligibility Criteria** | 103 | 12.8% | Income limits, landholding criteria, age limits, disqualifications |
| **Financial Assistance & Benefits** | 58 | 7.2% | Capital investment subsidies, pension matrices, monthly amounts |
| **Conditions & Implementation Rules** | 45 | 5.6% | Operational modalities, lease terms, verification protocols |
| **Application Procedure** | 33 | 4.1% | Online portal steps, block submission, timeline for sanction |

---

## 6. Table Isolation & Content Type Verification

In the repaired pipeline, tables extracted via PyMuPDF `find_tables()` are converted to clean Markdown and stored as standalone vector records with `content_type="table"`. Text chunks are stored with `content_type="text"`.

- **Standalone Table Chunks**: 165
- **Standard Text Chunks**: 639
- **Chunks with `has_tables=True`**: 165

Example Isolated Table Chunk (`MKUY_PDF.pdf`, Page 25):
```markdown
| Enterprise Category | Capital Investment Subsidy | Maximum Ceiling |
| ------------------- | -------------------------- | --------------- |
| General Category    | 40% of capital investment  | Rs. 50.00 Lakh  |
| SC / ST / Women / PwD | 50% of capital investment | Rs. 1.00 Crore  |
```

---

## 7. Multilingual Retrieval Evaluation

| Query | Language | Expected Scheme | Retrieved Top Hit | Relevance & Provenance |
| :--- | :---: | :---: | :---: | :---: |
| *What are the eligibility criteria for commercial agri-enterprise under MKUY?* | English | MKUY | `MKUY Operational Guidelines` (Page 14, Checklists) | **Accurate** (Official agri.odisha.gov.in PDF) |
| *ମୁଖ୍ୟମନ୍ତ୍ରୀ କୃଷି ଉଦ୍ୟୋଗ ଯୋଜନାରେ କେତେ ସବସିଡି ମିଳେ?* | Odia | MKUY | `MKUY Operational Guidelines` (Annexure IV, Capital Subsidy) | **Accurate** (Official agri.odisha.gov.in PDF) |
| *What benefits are provided to senior citizens under ABADANA scheme in Odisha?* | English | ABADANA | `ABADANA Scheme Guidelines` (Financial Assistance Section) | **Accurate** (Official ssepd.odisha.gov.in PDF) |
| *Odisha me Rights of Persons with Disabilities rules ke tahat kya suvidha hai?* | Hindi / Hinglish | ORPwD | `Odisha Rights of Persons with Disabilities Rules` (Rule 1) | **Accurate** (Official ssepd.odisha.gov.in PDF) |
| *How are Women SHGs selected for health and livelihood activities under Mission Shakti in Odisha?* | English | Mission Shakti | `Mission Shakti Selection of WSHGs Health Guidelines` | **Accurate** (Official missionshakti.odisha.gov.in PDF) |

---

## 8. Test Suite & Verification Results

Full automated regression test execution:
```bash
venv/bin/pytest tests/ -v
======================= 94 passed, 9 warnings in 38.51s ========================
```
- Total test cases: 94
- Passing: 94 (100%)
- Failing: 0
- Specific verification tests passed:
  - `test_resolve_department_command` (P1–P14 command resolution)
  - `test_score_document_relevance` (Relevance filter $\ge 0.60$, tender/recruitment rejection)
  - `test_verify_official_provenance` (Official domain whitelist verification)
  - `test_clean_extracted_text` (NIC footers and page noise removal)
  - `test_chunk_document_semantically` (Semantic chunking and section detection)
  - `test_chunk_document_semantically_table_isolation` (Standalone table chunk extraction)
  - `test_rule_1_zero_synthetic_documents` (404 rejection with zero synthetic fallback)
  - `test_end_to_end_single_department_lifecycle` (Phase 1–12 lifecycle execution)

---

## 9. Current Corpus State & Stop Condition

### Global State (`data/corpus_state.json`)
```json
{
  "P1": {
    "priority": "P1",
    "department": "Agriculture & Farmers' Empowerment",
    "status": "completed",
    "documents": 3,
    "chunks": 532
  },
  "P2": {
    "priority": "P2",
    "department": "Social Security & Empowerment of Persons with Disabilities",
    "status": "completed",
    "documents": 4,
    "chunks": 156
  },
  "P3": {
    "priority": "P3",
    "department": "Women & Child Development / Mission Shakti",
    "status": "completed",
    "documents": 3,
    "chunks": 116
  },
  "P4": {
    "priority": "P4",
    "department": "ST & SC Development",
    "status": "pending",
    "documents": 0,
    "chunks": 0
  }
}
```

> [!CAUTION]
> **PIPELINE STOPPED**: In accordance with the system specification, processing halted after completing P1–P3 repair and verification. P4 (ST & SC Development) has NOT been started. Execution is paused awaiting explicit user command.
