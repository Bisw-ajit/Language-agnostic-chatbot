# Evaluation & Benchmark Methodology

## Overview
The Language Agnostic Chatbot includes an automated, reproducible benchmark and validation suite located in `evaluation/run_benchmarks.py`. It tests retrieval quality, reranking gains, cross-lingual equivalence, adversarial Hinglish robustness, grounding checks, and real-world latency.

---

## 1. Benchmark Execution

To run the complete benchmark suite:
```bash
source venv/bin/activate
python evaluation/run_benchmarks.py
```
This runs all 8 validation stages and automatically updates `evaluation/metrics.json`, `evaluation/results.json`, and `evaluation/report.md`.

---

## 2. Evaluation Stages & Metrics

| Stage | Focus Area | Key Metrics |
|---|---|---|
| **1. Language Detection** | Multilingual accuracy across English, Hindi, Hinglish, and Odia queries | Accuracy (%), Macro F1 |
| **2. Retrieval & Reranker** | Dense vs Sparse vs Hybrid RRF vs Reranked | Recall@k, MRR@k, Precision@k |
| **3. Cross-Language Equivalence** | Retrieval rank similarity when asking same question in Odia, Hindi, or English | Jaccard overlap, Rank correlation |
| **4. Hinglish Adversarial** | Phonetic spelling variation, typo tolerance, mixed script | Hit Rate (%), Semantic match score |
| **5. Evidence Validation** | High, Medium, and Insufficient grounding signals, Contradiction detection | Precision on fallbacks, Contradiction recall |
| **6. Versioning & Deduplication**| Archiving of superseded policies, SHA-256 duplicate detection | Deduplication rate, Active chunk purity |
| **7. Citation & Grounding** | Citation accuracy, hallucination prevention | Citation precision, Grounding score |
| **8. Performance & Latency** | Pipeline stage duration breakdown | P50, P95, P99 latency (ms) |

---

## 3. Real Production Latency Baseline

In contrast to initial prototype claims of "1.18ms total latency" (which only measured in-memory token lookup without LLM generation), real-world production measurements reflect:
- **Retrieval (Vector + BM25 + RRF)**: 10 – 35 ms
- **Reranker (Semantic-Lexical)**: 2 – 8 ms
- **Evidence Validation**: 0.5 – 2 ms
- **LLM Generation (Gemini Cloud API)**: 800 – 2,500 ms (depending on network and generation length)
- **End-to-End Total Latency**: ~0.8 – 2.6 seconds (with streaming token delivery starting in ~300ms)
