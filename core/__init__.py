"""
Core module for Local Semantic Search Engine.

This module contains the fundamental components for document processing,
embedding generation, and vector storage.
"""

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore
from .file_loader import FileLoader
from .chunker import TextChunker
from .indexer import DocumentIndexer
from .search_engine import SearchEngine

__all__ = [
    'EmbeddingGenerator',
    'VectorStore',
    'FileLoader',
    'TextChunker',
    'DocumentIndexer',
    'SearchEngine',
]

__version__ = '0.1.0'