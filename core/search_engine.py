"""
Hybrid search engine combining semantic and keyword search.
"""

import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re
from collections import Counter
import math

from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Container for search results."""
    chunk_id: str
    text: str
    metadata: Dict[str, Any]
    score: float
    semantic_score: float
    keyword_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'chunk_id': self.chunk_id,
            'text': self.text,
            'metadata': self.metadata,
            'score': self.score,
            'semantic_score': self.semantic_score,
            'keyword_score': self.keyword_score
        }


class SearchEngine:
    """
    Hybrid search engine combining semantic and keyword-based retrieval.
    
    Features:
    - Semantic search using embeddings
    - Keyword search using BM25-like scoring
    - Configurable weight balance
    - Metadata filtering
    - Result deduplication and ranking
    """
    
    def __init__(
        self,
        embedder: EmbeddingGenerator,
        vector_store: VectorStore,
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        min_score: float = 0.3
    ):
        """
        Initialize the search engine.
        
        Args:
            embedder: Embedding generator
            vector_store: Vector storage
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            min_score: Minimum score threshold for results
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.semantic_weight = semantic_weight
        self.keyword_weight = keyword_weight
        self.min_score = min_score
        
        # Validate weights
        if not math.isclose(semantic_weight + keyword_weight, 1.0, rel_tol=1e-5):
            logger.warning("Weights don't sum to 1.0, normalizing...")
            total = semantic_weight + keyword_weight
            self.semantic_weight = semantic_weight / total
            self.keyword_weight = keyword_weight / total
        
        logger.info(
            f"SearchEngine initialized (semantic: {self.semantic_weight:.2f}, "
            f"keyword: {self.keyword_weight:.2f})"
        )
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: Optional[Dict[str, Any]] = None,
        semantic_only: bool = False
    ) -> List[SearchResult]:
        """
        Perform hybrid search.
        
        Args:
            query: Search query
            top_k: Number of results to return
            filters: Metadata filters (e.g., {"file_type": "pdf"})
            semantic_only: Use only semantic search (faster)
            
        Returns:
            List of SearchResult objects, ranked by score
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return []
        
        logger.info(f"Searching for: '{query}' (top_k: {top_k})")
        
        # Get semantic results (retrieve more for reranking)
        retrieve_k = top_k * 3 if not semantic_only else top_k
        semantic_results = self._semantic_search(query, retrieve_k, filters)
        
        if semantic_only or self.keyword_weight == 0:
            # Return only semantic results
            results = [
                SearchResult(
                    chunk_id=res['id'],
                    text=res['document'],
                    metadata=res['metadata'],
                    score=res['score'],
                    semantic_score=res['score'],
                    keyword_score=0.0
                )
                for res in semantic_results[:top_k]
            ]
            
            logger.info(f"Found {len(results)} semantic results")
            return results
        
        # Compute keyword scores for semantic results
        scored_results = []
        
        for res in semantic_results:
            keyword_score = self._compute_keyword_score(query, res['document'])
            
            # Combine scores
            combined_score = (
                self.semantic_weight * res['score'] +
                self.keyword_weight * keyword_score
            )
            
            if combined_score >= self.min_score:
                scored_results.append(SearchResult(
                    chunk_id=res['id'],
                    text=res['document'],
                    metadata=res['metadata'],
                    score=combined_score,
                    semantic_score=res['score'],
                    keyword_score=keyword_score
                ))
        
        # Sort by combined score
        scored_results.sort(key=lambda x: x.score, reverse=True)
        
        # Return top k
        results = scored_results[:top_k]
        
        logger.info(f"Found {len(results)} hybrid results")
        return results
    
    def _semantic_search(
        self,
        query: str,
        top_k: int,
        filters: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using embeddings.
        
        Returns:
            List of dictionaries with 'id', 'document', 'metadata', 'score'
        """
        # Generate query embedding
        query_embedding = self.embedder.generate_query_embedding(query)
        
        # Search vector store
        results = self.vector_store.search(
            query_embedding=query_embedding,
            n_results=top_k,
            filters=filters
        )
        
        # Convert distances to similarity scores (1 - distance for cosine)
        # ChromaDB returns distances, lower is better for cosine
        formatted_results = []
        
        for i in range(len(results['ids'])):
            # Convert distance to similarity score
            distance = results['distances'][i]
            similarity = max(0.0, 1.0 - distance)  # Ensure non-negative
            
            formatted_results.append({
                'id': results['ids'][i],
                'document': results['documents'][i],
                'metadata': results['metadatas'][i],
                'score': similarity
            })
        
        return formatted_results
    
    def _compute_keyword_score(self, query: str, document: str) -> float:
        """
        Compute BM25-like keyword matching score.
        
        Args:
            query: Search query
            document: Document text
            
        Returns:
            Keyword score between 0 and 1
        """
        # Tokenize and normalize
        query_terms = self._tokenize(query)
        doc_terms = self._tokenize(document)
        
        if not query_terms or not doc_terms:
            return 0.0
        
        # Count term frequencies
        doc_term_freq = Counter(doc_terms)
        doc_length = len(doc_terms)
        
        # BM25 parameters
        k1 = 1.5  # Term frequency saturation
        b = 0.75  # Length normalization
        avgdl = 100  # Average document length (approximate)
        
        score = 0.0
        
        for term in query_terms:
            if term in doc_term_freq:
                tf = doc_term_freq[term]
                
                # BM25 term score
                numerator = tf * (k1 + 1)
                denominator = tf + k1 * (1 - b + b * (doc_length / avgdl))
                
                term_score = numerator / denominator
                score += term_score
        
        # Normalize by query length
        if len(query_terms) > 0:
            score = score / len(query_terms)
        
        # Normalize to 0-1 range (approximate)
        score = min(1.0, score / 3.0)
        
        return score
    
    @staticmethod
    def _tokenize(text: str) -> List[str]:
        """
        Tokenize text into lowercase terms.
        
        Args:
            text: Text to tokenize
            
        Returns:
            List of lowercase tokens
        """
        # Convert to lowercase
        text = text.lower()
        
        # Extract alphanumeric tokens
        tokens = re.findall(r'\w+', text)
        
        # Remove very short tokens
        tokens = [t for t in tokens if len(t) > 2]
        
        return tokens
    
    def search_by_file(
        self,
        file_path: str,
        query: Optional[str] = None,
        top_k: int = 10
    ) -> List[SearchResult]:
        """
        Search within a specific file.
        
        Args:
            file_path: Path to the file
            query: Optional search query (if None, returns all chunks)
            top_k: Number of results
            
        Returns:
            List of SearchResult objects
        """
        filters = {'file_path': file_path}
        
        if query:
            return self.search(query, top_k, filters)
        else:
            # Return all chunks from file
            results = self.vector_store.get_by_filter(filters, limit=top_k)
            
            return [
                SearchResult(
                    chunk_id=results['ids'][i],
                    text=results['documents'][i],
                    metadata=results['metadatas'][i],
                    score=1.0,
                    semantic_score=1.0,
                    keyword_score=0.0
                )
                for i in range(len(results['ids']))
            ]
    
    def get_similar_chunks(
        self,
        chunk_id: str,
        top_k: int = 5
    ) -> List[SearchResult]:
        """
        Find chunks similar to a given chunk.
        
        Args:
            chunk_id: ID of the reference chunk
            top_k: Number of similar chunks to find
            
        Returns:
            List of similar SearchResult objects
        """
        # Get the chunk
        results = self.vector_store.collection.get(
            ids=[chunk_id],
            include=["documents", "embeddings"]
        )
        
        if not results['ids']:
            logger.warning(f"Chunk not found: {chunk_id}")
            return []
        
        # Get embedding
        embedding = results['embeddings'][0]
        
        # Search for similar chunks (retrieve k+1 to exclude self)
        similar = self.vector_store.search(
            query_embedding=embedding,
            n_results=top_k + 1,
            filters=None
        )
        
        # Format results (exclude the original chunk)
        formatted_results = []
        
        for i in range(len(similar['ids'])):
            if similar['ids'][i] == chunk_id:
                continue  # Skip the original chunk
            
            distance = similar['distances'][i]
            similarity = max(0.0, 1.0 - distance)
            
            formatted_results.append(SearchResult(
                chunk_id=similar['ids'][i],
                text=similar['documents'][i],
                metadata=similar['metadatas'][i],
                score=similarity,
                semantic_score=similarity,
                keyword_score=0.0
            ))
        
        return formatted_results[:top_k]