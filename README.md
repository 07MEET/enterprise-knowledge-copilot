# Enterprise Knowledge Copilot (EKC)

Enterprise Knowledge Copilot is a production-grade, local-first **Retrieval-Augmented Generation (RAG)** system designed to answer questions from corporate policies, SOPs, and governance documents (such as CSR Policies, Whistleblower Policies, and ESG Reports) with verified citations and physical page alignments.

This system combines advanced layout-aware parsing, hybrid search, citation alignment verification, and automated evaluation metrics into a modular, deployable architecture.

---

## 🏗️ System Architecture

```text
               +----------------------------------+
               |        Streamlit Frontend        |
               +----------------------------------+
                                |
                                | HTTP / REST API
                                v
               +----------------------------------+
               |         FastAPI Backend          |
               +----------------------------------+
                 /                              \
                / Ingestion                      \ Query
               /  Pipeline                        \ Path
              v                                    v
  +-----------------------+            +-----------------------+
  |  Docling PDF Parser   |            |   Query Pre-process   |
  |  (Forced full OCR)    |            |   (Acronym Expansion) |
  +-----------------------+            +-----------------------+
              |                                    |
              v                                    v
  +-----------------------+            +-----------------------+
  | Chunker + Page Mapper |            | Hybrid Retriever (10) |
  | (Overlap & physical)  |            | (Dense + Sparse search)
  +-----------------------+            +-----------------------+
       /             \                             /         \
      /               \                           /           \
     v                 v                         v             v
+----------+     +----------+               +----------+  +----------+
| ChromaDB |     |   BM25   |               | ChromaDB |  |   BM25   |
| (Vector) |     | (Sparse) |               | (Vector) |  | (Sparse) |
+----------+     +----------+               +----------+  +----------+
                                                 \             /
                                                  \           /
                                                   v         v
                                            +-----------------------+
                                            | LLM Generation Engine |
                                            | (Llama 3.2 / Gemini)  |
                                            +-----------------------+
                                                        |
                                                        v
                                            +-----------------------+
                                            |   Citation Verifier   |
                                            | (Sentence Alignment)  |
                                            +-----------------------+
                                                        |
                                                        v
                                            +-----------------------+
                                            | Sequential Citation   |
                                            |  Formatting & Filter  |
                                            +-----------------------+
                                                        |
                                                        v
                                            +-----------------------+
                                            |    Streamlit Render   |
                                            +-----------------------+
```

---

## ⚡ Key Features

* **Advanced Layout-Aware PDF Ingestion**: Uses **Docling** with OCR capabilities to parse multi-column tables, scanned text, and structured lists, converting them to clean Markdown.
* **Page-Mapped Chunking**: Track chunk boundaries and map every piece of text back to its **physical PDF page number** for audit-ready compliance citations.
* **Hybrid Search with RRF**: Merges dense vector embeddings (ChromaDB using `BGE-Large-EN-v1.5`) and sparse keyword matches (BM25) using **Reciprocal Rank Fusion (RRF)** for high-recall document matching.
* **Factual Citation Auditor**: An alignment verifier that performs verbatim checks, proper noun matching (resolves exact named entities instantly), and semantic entailment checking to eliminate hallucinations and generate a trustworthiness score.
* **Streamlit Admin Dashboard**: Chat window with citation breakdown (file, page, section), raw PDF ingestion uploader, and a full **Knowledge Base Manager** to inspect indexed files and trigger deletions.
* **20-Case LLM-as-a-Judge Evaluator**: Automated RAG evaluation benchmark measuring Faithfulness, Context Recall, Answer Relevance, and Refusal Accuracy.
* **Zero-Config Dockerized Deployment**: Run the frontend, backend, local database, Ollama, and auto-download Llama 3.2 with a single CLI command.

---

## 📁 Repository Structure

```text
├── app/
│   ├── api/            # FastAPI Endpoint Routes (query, documents, health)
│   ├── config/         # App configuration settings and directory setups
│   ├── embeddings/     # Embeddings models abstraction factory
│   ├── evaluation/     # Golden dataset and evaluator grading loops
│   ├── generation/     # Prompt configurations & response generators
│   ├── ingestion/      # Docling parsing, metadata extraction, & page chunkers
│   ├── models/         # Pydantic schemas for request/response payloads
│   ├── retrieval/      # Dense ChromaDB search and BM25 retrievers
│   ├── services/       # query_service.py orchestrator pipeline
│   ├── storage/        # ChromaDB setup and CRUD operations
│   ├── utils/          # Rate limiters & JSON clean helpers
│   └── verification/   # Citation verifier and claim alignment engine
├── data/               # Persistent raw PDFs, processed markdown, & Chroma databases
├── streamlit_app/      # Streamlit user interface dashboard file
├── docs/               # Markdown documentation and evaluations reports
├── eval.py             # CLI evaluation benchmark runner
├── Dockerfile          # Multi-stage Docker container build
├── docker-compose.yml  # Docker multi-service configuration
└── requirements.txt    # Application dependencies list
```

---

## 🚀 Getting Started

### Method 1: Running with Docker (Recommended)
You only need **Docker Desktop** installed. 

1. Clone the repository and navigate into it:
   ```bash
   git clone <your-repo-url>
   cd enterprise-knowledge-copilot
   ```
2. Build and run the stack:
   ```bash
   docker-compose up --build
   ```
   *This starts the local database, spins up Ollama, auto-downloads the Llama 3.2 model, runs the FastAPI backend, and starts the Streamlit dashboard.*
3. Open **`http://localhost:8501`** in your browser.

---

### Method 2: Running Locally (Manual Setup)

#### 1. Setup Environment
Ensure Python 3.10+ is installed. Create a virtual environment or Conda environment:
```bash
conda create -n ekc python=3.11 -y
conda activate ekc
pip install -r requirements.txt
```

#### 2. Configure Settings
Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
```
Update configuration parameters:
- `USE_LOCAL=True` to use Ollama locally, or `False` to run on Google Gemini.
- Set `GEMINI_API_KEY` if running cloud models.

#### 3. Run Ollama (If local)
Make sure Ollama is running and Llama 3.2 is downloaded:
```bash
ollama run llama3.2
```

#### 4. Run Services
Start the FastAPI server in one terminal:
```bash
uvicorn app.main:app --reload --port 8000
```
Start the Streamlit dashboard in a second terminal:
```bash
streamlit run streamlit_app/dashboard.py
```
Visit **`http://localhost:8501`** to use the application.

---

## 📊 Running Evaluation Reports

To run the custom 20-question RAG evaluation scorecard:
```bash
python eval.py
```
This runs live search queries against your indexes, judges the answers, and generates a detailed scorecard report stored at **`docs/evaluation_report.md`**.
