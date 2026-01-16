# Local Semantic Search Engine (Desktop)

A local, privacy-first desktop application for searching documents using semantic embeddings, keyword matching, or a combination of both.  
All indexing and search happen locally. An optional AI layer can be enabled for document-based Q&A.

This project is intended as a **personal or internal tool**, not a hosted service or public search engine.

---

## Overview

The application monitors selected folders, extracts text from supported documents, splits content into chunks, generates embeddings, and stores them in a local vector database.

Queries are resolved using:
- Semantic similarity (embeddings)
- Keyword relevance (BM25)
- Or a weighted hybrid of both

An optional Retrieval-Augmented Generation (RAG) layer can be enabled to answer questions using only local documents.

---

## Features

### Search
- Semantic search using sentence embeddings
- Keyword search using BM25
- Hybrid scoring with configurable weights
- Semantic-only mode for faster conceptual queries
- Minimum relevance threshold filtering

### Document Support
- PDF
- DOCX
- TXT / Markdown
- Optional OCR for scanned documents (Tesseract)

### Desktop Interface
- Built with PySide6 (Qt)
- Sidebar navigation
- Search and Chat views
- Result list with relevance scores
- Document preview pane
- Status and indexing feedback

### Optional AI Layer
- Retrieval-Augmented Generation (RAG)
- Local GGUF models via `llama-cpp-python`
- Or external APIs (OpenAI / Anthropic)
- Fully optional; search works without any LLM

---

## How Search Works

### Hybrid Mode (Default)

Hybrid search combines semantic similarity and keyword relevance.

1. The query is converted into an embedding
2. Relevant document chunks are retrieved via cosine similarity
3. Keywords are scored using BM25
4. Scores are combined using configurable weights
5. Results below a minimum score are discarded

```

final_score =
(semantic_score × semantic_weight)

* (keyword_score  × keyword_weight)

```

Typical defaults:
- Semantic weight: 0.7  
- Keyword weight: 0.3  
- Minimum score: 0.3  

### Semantic-Only Mode

Semantic-only mode skips keyword matching and relies purely on embeddings.  
It is faster and works best for conceptual or exploratory queries.

---

## Project Structure

```

core/
├─ ingestion/
│   ├─ file_watcher.py
│   ├─ loaders/
│   └─ chunker.py
│
├─ embeddings/
│   └─ embedding_model.py
│
├─ vector_store/
│   └─ chroma_manager.py
│
├─ search/
│   ├─ hybrid_search.py
│   └─ bm25.py

gui/
├─ main_window.py
├─ search_tab.py
├─ chat_tab.py
└─ settings_dialog.py

llm/
├─ local_llm.py
└─ api_llm.py

utils/
logger.py
main.py
requirements.txt

````

---

## Technology Stack

- UI: PySide6 (Qt)
- Embeddings: BGE-small
- Vector database: ChromaDB
- OCR: Tesseract (optional)
- Search: Semantic similarity + BM25
- LLMs: Local GGUF models or API-based providers

---

## Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourname/local-semantic-search
cd local-semantic-search
````

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate
# Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. (Optional) Install OCR

```bash
sudo apt install tesseract-ocr
```

### 5. Run the application

```bash
python main.py
```

---

## Configuration

Configuration is handled via the Settings dialog.

### General

* Watched folders
* Supported file types
* Re-index and database reset

### LLM

* Mode: None / Local / API
* Local model path (GGUF)
* API provider and key

### Advanced

* Chunk size and overlap
* Search weights
* Minimum relevance score
* OCR enable/disable

---

## AI Chat (RAG)

When enabled, the chat interface:

1. Retrieves the most relevant document chunks
2. Injects them into the LLM context
3. Generates answers grounded strictly in local documents

If no LLM is configured, the application functions as a search-only tool.

---

## Design Principles

* Local-first and offline-capable
* No mandatory AI dependency
* Transparent scoring
* Incremental indexing
* Minimal external services

---

## License

MIT License.

```
