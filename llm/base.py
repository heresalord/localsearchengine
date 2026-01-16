"""
Base classes and interfaces for LLM integration.
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Iterator
from enum import Enum

logger = logging.getLogger(__name__)


class LLMMode(Enum):
    """LLM operation modes."""
    NONE = "none"
    LOCAL = "local"
    API = "api"


class APIProvider(Enum):
    """Supported API providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """Configuration for LLM."""
    mode: str = "none"  # "none", "local", "api"
    
    # Local model settings
    local_model_path: Optional[str] = None
    n_ctx: int = 4096  # Context window size
    n_threads: int = 4  # CPU threads
    n_gpu_layers: int = 0  # GPU acceleration (0 = CPU only)
    
    # API settings
    api_provider: Optional[str] = None  # "openai", "anthropic"
    api_key: Optional[str] = None
    api_model: str = "gpt-3.5-turbo"  # Default model
    api_base_url: Optional[str] = None  # For custom endpoints
    
    # Generation settings
    temperature: float = 0.7
    max_tokens: int = 1000
    top_p: float = 0.9
    
    # RAG settings
    max_context_chunks: int = 5  # Max chunks to include in context
    
    def validate(self) -> bool:
        """
        Validate configuration.
        
        Returns:
            True if valid, False otherwise
        """
        if self.mode == "none":
            return True
        
        elif self.mode == "local":
            if not self.local_model_path:
                logger.error("local_model_path required for local mode")
                return False
            return True
        
        elif self.mode == "api":
            if not self.api_key or not self.api_provider:
                logger.error("api_key and api_provider required for API mode")
                return False
            return True
        
        else:
            logger.error(f"Invalid mode: {self.mode}")
            return False


@dataclass
class LLMResponse:
    """Response from LLM."""
    text: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def success(self) -> bool:
        """Check if response was successful."""
        return self.error is None


class BaseLLM(ABC):
    """
    Abstract base class for LLM implementations.
    
    All LLM classes must implement these methods.
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize LLM.
        
        Args:
            config: LLM configuration
        """
        if not config.validate():
            raise ValueError("Invalid LLM configuration")
        
        self.config = config
        self._is_loaded = False
        
        logger.info(f"Initializing {self.__class__.__name__}")
    
    @abstractmethod
    def load(self) -> bool:
        """
        Load the model/initialize API client.
        
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def unload(self) -> None:
        """Unload model and free resources."""
        pass
    
    @abstractmethod
    def generate(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text from prompt.
        
        Args:
            prompt: Input prompt
            stream: Whether to stream response
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse object
        """
        pass
    
    @abstractmethod
    def generate_stream(
        self,
        prompt: str,
        **kwargs
    ) -> Iterator[str]:
        """
        Generate text with streaming.
        
        Args:
            prompt: Input prompt
            **kwargs: Additional generation parameters
            
        Yields:
            Text chunks
        """
        pass
    
    def answer_question(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        stream: bool = False
    ) -> LLMResponse:
        """
        Answer a question using retrieved context (RAG).
        
        Args:
            question: User's question
            context_chunks: Retrieved document chunks
            stream: Whether to stream response
            
        Returns:
            LLMResponse with answer
        """
        # Build RAG prompt
        prompt = self._build_rag_prompt(question, context_chunks)
        
        # Generate answer
        return self.generate(prompt, stream=stream)
    
    def summarize_document(
        self,
        text: str,
        max_length: Optional[int] = None
    ) -> LLMResponse:
        """
        Summarize a document.
        
        Args:
            text: Document text
            max_length: Maximum summary length
            
        Returns:
            LLMResponse with summary
        """
        prompt = self._build_summary_prompt(text, max_length)
        return self.generate(prompt)
    
    def _build_rag_prompt(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]]
    ) -> str:
        """
        Build prompt for RAG (Retrieval-Augmented Generation).
        
        Args:
            question: User's question
            context_chunks: Retrieved chunks with 'text' and 'metadata'
            
        Returns:
            Formatted prompt
        """
        # Limit number of chunks
        chunks = context_chunks[:self.config.max_context_chunks]
        
        # Build context string
        context_parts = []
        for i, chunk in enumerate(chunks, 1):
            text = chunk.get('text', '')
            metadata = chunk.get('metadata', {})
            file_name = metadata.get('file_name', 'Unknown')
            
            context_parts.append(f"[Document {i}: {file_name}]\n{text}\n")
        
        context = "\n".join(context_parts)
        
        # Build prompt
        prompt = f"""You are a helpful assistant that answers questions based on the provided documents.

Context:
{context}

Question: {question}

Instructions:
- Answer based only on the information in the provided documents
- If the answer is not in the documents, say "I cannot find that information in the provided documents"
- Cite which document(s) you used to answer
- Be concise and accurate

Answer:"""
        
        return prompt
    
    def _build_summary_prompt(
        self,
        text: str,
        max_length: Optional[int] = None
    ) -> str:
        """
        Build prompt for summarization.
        
        Args:
            text: Text to summarize
            max_length: Target summary length
            
        Returns:
            Formatted prompt
        """
        length_instruction = ""
        if max_length:
            length_instruction = f" in about {max_length} words"
        
        prompt = f"""Please provide a concise summary of the following text{length_instruction}:

Text:
{text}

Summary:"""
        
        return prompt
    
    @property
    def is_loaded(self) -> bool:
        """Check if model is loaded."""
        return self._is_loaded
    
    @property
    def supports_streaming(self) -> bool:
        """Check if streaming is supported."""
        return True  # Override in subclass if not supported
    
    def get_info(self) -> Dict[str, Any]:
        """
        Get information about the LLM.
        
        Returns:
            Dictionary with model info
        """
        return {
            'mode': self.config.mode,
            'loaded': self.is_loaded,
            'supports_streaming': self.supports_streaming,
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
        }