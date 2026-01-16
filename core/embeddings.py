"""
Embedding generation using sentence-transformers.
"""

import logging
from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates semantic embeddings for text using BGE-small model.
    
    This class handles:
    - Model loading and caching
    - Batch processing for efficiency
    - Normalization for cosine similarity
    """
    
    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", device: str = "cpu"):
        """
        Initialize the embedding generator.
        
        Args:
            model_name: HuggingFace model identifier
            device: 'cpu' or 'cuda' for GPU acceleration
        """
        self.model_name = model_name
        self.device = device
        self._model = None
        self.embedding_dim = 384  # BGE-small dimension
        
        logger.info(f"Initializing EmbeddingGenerator with model: {model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy load the model on first use."""
        if self._model is None:
            logger.info(f"Loading model: {self.model_name}")
            self._model = SentenceTransformer(self.model_name, device=self.device)
            logger.info("Model loaded successfully")
        return self._model
    
    def generate(self, texts: Union[str, List[str]], batch_size: int = 32) -> np.ndarray:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Single text or list of texts
            batch_size: Number of texts to process at once
            
        Returns:
            numpy array of shape (n_texts, embedding_dim)
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if not texts:
            return np.array([])
        
        logger.debug(f"Generating embeddings for {len(texts)} texts")
        
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                show_progress_bar=len(texts) > 100,
                normalize_embeddings=True  # L2 normalization for cosine similarity
            )
            
            logger.debug(f"Generated embeddings shape: {embeddings.shape}")
            return embeddings
            
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise
    
    def generate_query_embedding(self, query: str) -> np.ndarray:
        """
        Generate embedding for a search query.
        
        For BGE models, queries should be prefixed for better performance.
        
        Args:
            query: Search query text
            
        Returns:
            numpy array of shape (embedding_dim,)
        """
        # BGE models perform better with query prefix
        prefixed_query = f"Represent this sentence for searching relevant passages: {query}"
        
        embedding = self.generate(prefixed_query, batch_size=1)
        return embedding[0] if len(embedding.shape) > 1 else embedding
    
    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score between -1 and 1
        """
        return float(np.dot(embedding1, embedding2))
    
    def unload_model(self):
        """Free up memory by unloading the model."""
        if self._model is not None:
            logger.info("Unloading embedding model")
            del self._model
            self._model = None
            
            # Force garbage collection for GPU memory
            import gc
            gc.collect()
            
            if self.device == "cuda":
                import torch
                torch.cuda.empty_cache()