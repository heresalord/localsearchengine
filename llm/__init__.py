"""
LLM module for Local Semantic Search Engine.

This module provides optional language model integration for:
- Question answering over retrieved documents (RAG)
- Document summarization
- Contextual chat

Supports:
- Local GGUF models (llama.cpp)
- Online APIs (OpenAI, Anthropic, etc.)
"""

from .base import BaseLLM, LLMConfig, LLMResponse
from .local_model import LocalLLM
from .api_model import APILLM

__all__ = [
    'BaseLLM',
    'LLMConfig',
    'LLMResponse',
    'LocalLLM',
    'APILLM',
]

__version__ = '0.1.0'


def create_llm(config: LLMConfig) -> BaseLLM:
    """
    Factory function to create appropriate LLM instance.
    
    Args:
        config: LLM configuration
        
    Returns:
        BaseLLM instance (LocalLLM or APILLM)
        
    Raises:
        ValueError: If mode is invalid or configuration is incomplete
    """
    if config.mode == "none":
        raise ValueError("Cannot create LLM with mode='none'")
    
    elif config.mode == "local":
        if not config.local_model_path:
            raise ValueError("local_model_path required for local mode")
        return LocalLLM(config)
    
    elif config.mode == "api":
        if not config.api_key:
            raise ValueError("api_key required for API mode")
        if not config.api_provider:
            raise ValueError("api_provider required for API mode")
        return APILLM(config)
    
    else:
        raise ValueError(f"Invalid LLM mode: {config.mode}")