"""
Text chunking for optimal embedding and retrieval.
"""

import logging
from typing import List, Dict, Any
import re

logger = logging.getLogger(__name__)


class TextChunker:
    """
    Splits text into semantically meaningful chunks.
    
    Features:
    - Configurable chunk size and overlap
    - Respects sentence boundaries
    - Preserves context with overlap
    - Handles edge cases (short texts, empty strings)
    """
    
    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 200,
        min_chunk_size: int = 50
    ):
        """
        Initialize the text chunker.
        
        Args:
            chunk_size: Target size for each chunk (in characters)
            chunk_overlap: Number of characters to overlap between chunks
            min_chunk_size: Minimum chunk size to keep
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size
        
        # Sentence boundary regex (simple but effective)
        self.sentence_endings = re.compile(r'(?<=[.!?])\s+')
        
        logger.info(
            f"TextChunker initialized (size: {chunk_size}, "
            f"overlap: {chunk_overlap}, min: {min_chunk_size})"
        )
    
    def chunk(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into chunks with metadata.
        
        Args:
            text: Text to chunk
            metadata: Base metadata to attach to each chunk
            
        Returns:
            List of dictionaries with 'text' and 'metadata'
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to chunker")
            return []
        
        # Clean text
        text = self._clean_text(text)
        
        # If text is short, return as single chunk
        if len(text) <= self.chunk_size:
            return [{
                'text': text,
                'metadata': {
                    **metadata,
                    'chunk_index': 0,
                    'total_chunks': 1,
                    'char_count': len(text)
                }
            }]
        
        # Split into sentences first
        sentences = self._split_sentences(text)
        
        # Group sentences into chunks
        chunks = self._create_chunks(sentences)
        
        # Build result with metadata
        result = []
        for i, chunk_text in enumerate(chunks):
            if len(chunk_text.strip()) >= self.min_chunk_size:
                result.append({
                    'text': chunk_text,
                    'metadata': {
                        **metadata,
                        'chunk_index': i,
                        'total_chunks': len(chunks),
                        'char_count': len(chunk_text)
                    }
                })
        
        logger.debug(f"Created {len(result)} chunks from {len(text)} chars")
        return result
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        sentences = self.sentence_endings.split(text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _create_chunks(self, sentences: List[str]) -> List[str]:
        """
        Group sentences into chunks respecting size and overlap.
        
        Args:
            sentences: List of sentences
            
        Returns:
            List of chunk texts
        """
        if not sentences:
            return []
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        i = 0
        while i < len(sentences):
            sentence = sentences[i]
            sentence_len = len(sentence)
            
            # If single sentence exceeds chunk size, split it
            if sentence_len > self.chunk_size:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                    current_chunk = []
                    current_size = 0
                
                # Split long sentence by character count
                sub_chunks = self._split_long_sentence(sentence)
                chunks.extend(sub_chunks)
                i += 1
                continue
            
            # Check if adding this sentence would exceed chunk size
            if current_size + sentence_len > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append(' '.join(current_chunk))
                
                # Start new chunk with overlap
                overlap_chunk = self._get_overlap(current_chunk)
                current_chunk = overlap_chunk
                current_size = sum(len(s) for s in current_chunk)
            else:
                # Add sentence to current chunk
                current_chunk.append(sentence)
                current_size += sentence_len
                i += 1
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def _get_overlap(self, sentences: List[str]) -> List[str]:
        """
        Get sentences for overlap from end of current chunk.
        
        Args:
            sentences: Current chunk sentences
            
        Returns:
            Sentences for overlap
        """
        overlap_sentences = []
        overlap_size = 0
        
        # Work backwards from end of chunk
        for sentence in reversed(sentences):
            if overlap_size + len(sentence) <= self.chunk_overlap:
                overlap_sentences.insert(0, sentence)
                overlap_size += len(sentence)
            else:
                break
        
        return overlap_sentences
    
    def _split_long_sentence(self, sentence: str) -> List[str]:
        """
        Split a sentence that exceeds chunk size.
        
        Args:
            sentence: Long sentence
            
        Returns:
            List of sub-chunks
        """
        chunks = []
        words = sentence.split()
        
        current_chunk = []
        current_size = 0
        
        for word in words:
            word_len = len(word) + 1  # +1 for space
            
            if current_size + word_len > self.chunk_size and current_chunk:
                chunks.append(' '.join(current_chunk))
                current_chunk = [word]
                current_size = word_len
            else:
                current_chunk.append(word)
                current_size += word_len
        
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    @staticmethod
    def estimate_chunks(text: str, chunk_size: int = 800) -> int:
        """
        Estimate number of chunks for a text.
        
        Args:
            text: Text to estimate
            chunk_size: Target chunk size
            
        Returns:
            Estimated number of chunks
        """
        if not text:
            return 0
        return max(1, len(text) // chunk_size)