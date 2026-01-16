Local Semantic Search Engine (Desktop)

A local, privacy-first document search engine for desktop use.
It indexes files on your machine and allows fast retrieval using semantic embeddings, keyword search, or a combination of both. An optional AI layer can be enabled for document-based Q&A.

This tool is designed for personal or internal use, not as a hosted service.

Overview

The application watches selected folders, extracts text from supported documents, chunks and embeds the content, and stores it in a local vector database. Queries are resolved using either:

Semantic similarity (embeddings)

Keyword relevance (BM25)

Or a weighted combination of both

All data remains local unless an external LLM API is explicitly configured.

Features
Search

Semantic search using sentence embeddings

Keyword search using BM25

Hybrid scoring with configurable weights

Semantic-only fast mode

Minimum relevance threshold

Document Support

PDF

DOCX

TXT / Markdown

Optional OCR for scanned documents (Tesseract)

Desktop Interface

Built with PySide6 (Qt)

Sidebar navigation

Search and Chat views

Result list with relevance scores

Document preview pane

Status and progress feedback

Optional AI Layer

Retrieval-Augmented Generation (RAG)

Local models via llama-cpp-python (GGUF)

Or external APIs (OpenAI / Anthropic)

Fully optional, with graceful fallback when disabled

How Search Works
Hybrid Mode (Default)

Hybrid search combines semantic similarity and keyword relevance.

The query is converted into an embedding

Similar document chunks are retrieved using cosine similarity

Keywords are scored using BM25

Scores are combined using configurable weights

Results below a minimum score are filtered out

final_score =
  (semantic_score × semantic_weight)
+ (keyword_score  × keyword_weight)


Typical defaults:

Semantic weight: 0.7

Keyword weight: 0.3

Minimum score: 0.3

Semantic-Only Mode

Semantic-only mode skips keyword matching and relies purely on embeddings.
It is faster and better suited for conceptual or exploratory queries.

Architecture
ingestion/
 ├─ file_watcher.py
 ├─ loaders/
 ├─ chunker.py

embeddings/
 ├─ embedding_model.py

vector_store/
 ├─ chroma_manager.py

search/
 ├─ hybrid_search.py
 ├─ bm25.py

ui/
 ├─ main_window.py
 ├─ search_tab.py
 ├─ chat_tab.py
 ├─ settings_dialog.py

llm/
 ├─ local_llm.py
 ├─ api_llm.py

logger.py
app.py

Technology Stack

UI: PySide6 (Qt)

Embeddings: BGE-small

Vector database: ChromaDB

OCR: Tesseract (optional)

Search: Semantic similarity + BM25

LLMs: Local GGUF models or API-based providers

Installation
1. Clone the repository
git clone https://github.com/yourname/local-semantic-search
cd local-semantic-search

2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate

3. Install dependencies
pip install -r requirements.txt

4. (Optional) Install OCR
sudo apt install tesseract-ocr

5. Run the application
python app.py

Configuration

All configuration is done through the Settings dialog.

General

Watched folders

Supported file types

Re-index and database reset

LLM

Mode: None / Local / API

Local model path (GGUF)

API provider and key

Advanced

Chunk size and overlap

Search weights

Minimum relevance score

OCR enable/disable

AI Chat (RAG)

When enabled, the chat interface performs the following steps:

Retrieve the most relevant document chunks

Inject them into the LLM context

Generate an answer grounded strictly in local documents

If no LLM is configured, the search functionality remains fully usable.

Design Principles

Local-first and offline-capable

No mandatory AI dependency

Transparent scoring

Incremental indexing

Minimal external services

License

MIT License.
