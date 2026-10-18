# 📋 Jira User Stories & Milestone Roadmap — Project Review 1
**Project Name:** Language Agnostic Chatbot (Multi-Layer Semantic Knowledge Orchestration)  
**Jira Project Board:** [LAC Board](https://giet-team-qeqz8md6.atlassian.net/jira/software/projects/LAC/list)  
**Team Members & Assignees:**
* **Student 1:** Sreesanth Panda (`23cseaiml083.sreesanthpanda@giet.edu`) — Backend Architecture, Ingestion & Storage
* **Student 2:** J Subham Acharye — Multilingual NLP Core & Hybrid Retrieval Engine
* **Student 3:** Nilesh Gourab Rout — Frontend UI, Admin Portal & Evaluation Suite

**Milestone Target:** Project Review 1  
**Current Completion:** ~62.9% (39 / 62 Story Points Done)

---

## 📊 Sprint Progress Breakdown

| Category | Count | Story Points | Percentage | Due Date Range | Jira Status |
| :--- | :---: | :---: | :---: | :---: | :---: |
| 🟢 **Completed (Sprint 1)** | **9** | **39 pts** | **62.9%** | **Aug 20 – Aug 30, 2026** *(Completed on time)* | `Done` |
| 🟡 **In Progress (Active Sprint)** | **4** | **16 pts** | **25.8%** | **Sept 20 – Oct 20, 2026** *(Active Sprint - Before Nov)* | `In Progress` |
| ⚪ **To Do (Phase 3 / Future Scope)** | **2** | **8 pts** | **12.9%** | **Oct 10 – Oct 28, 2026** *(Before November)* | `To Do` |
| **Total** | **15** | **62 pts** | **100%** | — | — |

---

## 🟢 1. Completed User Stories (9 Stories — 62.9% — Done before 30th August 2026)

| Jira Key | Summary & Acceptance Criteria | Assignee | Due Date | Priority | Points | Component | Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **[LAC-1](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-1)** | **US-01: User Authentication & Role-Based Access Control (RBAC)**<br/>• bcrypt password hashing & JWT token auth<br/>• Student & Admin role-based endpoints | Sreesanth Panda | **2026-08-20** | **Highest** | 5 pts | `Backend` | `Done` |
| **[LAC-2](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-2)** | **US-02: FastAPI Backend Core Architecture & Health Endpoints**<br/>• Modular router design with CORS for React Vite<br/>• `/api/health` monitoring endpoint | Sreesanth Panda | **2026-08-22** | **High** | 3 pts | `Backend` | `Done` |
| **[LAC-3](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-3)** | **US-03: Document Ingestion & Text Chunking Pipeline**<br/>• PDF text/metadata extraction via PyMuPDF<br/>• Recursive character splitting (500-token chunk, 50-token overlap) | Sreesanth Panda | **2026-08-25** | **Highest** | 5 pts | `Data Pipeline` | `Done` |
| **[LAC-4](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-4)** | **US-04: Dense Vector Storage & ChromaDB Indexing**<br/>• Persistent ChromaDB vector collection<br/>• Multilingual dense embeddings generation | Sreesanth Panda | **2026-08-27** | **Highest** | 5 pts | `Data Pipeline` | `Done` |
| **[LAC-5](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-5)** | **US-05: Multi-Language Query Detection (English, Hindi, Hinglish, Odia)**<br/>• Script detection for Devanagari & Odia<br/>• Latin-script Hinglish transliteration classification | J Subham Acharye | **2026-08-28** | **High** | 5 pts | `NLP Core` | `Done` |
| **[LAC-7](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-7)** | **US-07: Sparse Retrieval with BM25 Indexing**<br/>• Multilingual tokenization & stopword filtering<br/>• BM25 sparse keyword search scoring | J Subham Acharye | **2026-08-29** | **High** | 5 pts | `Search & Retrieval` | `Done` |
| **[LAC-8](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-8)** | **US-08: Reciprocal Rank Fusion (RRF) Hybrid Retriever**<br/>• RRF algorithm ($k=60$) combining dense + sparse search<br/>• Candidate deduplication & score merging | J Subham Acharye | **2026-08-30** | **Highest** | 5 pts | `Search & Retrieval` | `Done` |
| **[LAC-6](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-6)** | **US-06: Responsive Chat User Interface & Starter Query Cards**<br/>• Real-time message streaming chat window<br/>• Starter query cards across all 4 languages | Nilesh Gourab Rout | **2026-08-29** | **Medium** | 3 pts | `Frontend` | `Done` |
| **[LAC-10](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-10)** | **US-10: Admin Document Management & Metadata Tagging UI**<br/>• Document manager table with status & checksum<br/>• Drag-and-drop PDF upload uploader | Nilesh Gourab Rout | **2026-08-30** | **Medium** | 3 pts | `Frontend` | `Done` |

---

## 🟡 2. In-Progress User Stories (4 Stories — Active Sprint — Due before November 2026)

| Jira Key | Summary & Acceptance Criteria | Assignee | Due Date | Priority | Points | Component | Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **[LAC-13](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-13)** | **US-13: Unanswered Query Analytics & Admin Feedback Loop**<br/>• Logging low-confidence / fallback queries<br/>• Admin analytics dashboard for scheme knowledge gaps | Sreesanth Panda | **2026-10-15** | **Medium** | 3 pts | `Backend` | `In Progress` |
| **[LAC-9](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-9)** | **US-09: LLM Prompt Orchestration & Zero-Hallucination Guardrails**<br/>• Grounded system prompt templates<br/>• Confidence threshold fallback (<0.65) | J Subham Acharye | **2026-09-20** | **High** | 5 pts | `NLP Core` | `In Progress` |
| **[LAC-12](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-12)** | **US-12: Source Grounding & Interactive Citation References**<br/>• Interactive citation badges linked to source PDF page<br/>• Excerpt preview drawer modal | Nilesh Gourab Rout | **2026-09-25** | **High** | 3 pts | `Frontend` | `In Progress` |
| **[LAC-14](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-14)** | **US-14: Comprehensive Benchmark Evaluation Suite**<br/>• 100 question-answer benchmark dataset<br/>• Automated metrics (Recall@5, MRR, Latency) | Nilesh Gourab Rout | **2026-10-20** | **Medium** | 5 pts | `Testing & QA` | `In Progress` |

---

## ⚪ 3. To Do / Future Scope (2 Stories — Phase 3 — Due before November 2026)

| Jira Key | Summary & Acceptance Criteria | Assignee | Due Date | Priority | Points | Component | Status |
|:---|:---|:---|:---:|:---:|:---:|:---:|:---:|
| **[LAC-11](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-11)** | **US-11: Cross-Encoder Semantic Reranker Integration**<br/>• Cross-encoder inference on top-10 chunks<br/>• Optimizing Mean Reciprocal Rank (MRR) | J Subham Acharye | **2026-10-10** | **High** | 5 pts | `Search & Retrieval` | `To Do` |
| **[LAC-15](https://giet-team-qeqz8md6.atlassian.net/browse/LAC-15)** | **US-15: Docker Containerization & Production Deployment Config**<br/>• Multi-container Dockerfile & Compose configs<br/>• Volume persistence & healthcheck restart policies | Nilesh Gourab Rout | **2026-10-28** | **Low** | 3 pts | `DevOps` | `To Do` |
