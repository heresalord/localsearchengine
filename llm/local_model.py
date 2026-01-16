"""
Local LLM implementation using llama.cpp (GGUF models).
"""

import logging
from typing import Iterator, Optional, Dict, Any
from pathlib import Path

from .base import BaseLLM, LLMConfig, LLMResponse

logger = logging.getLogger(__name__)


class LocalLLM(BaseLLM):
    """
    Local LLM using llama-cpp-python.
    
    Supports:
    - GGUF format models (Llama, Mistral, etc.)
    - CPU and GPU inference
    - Streaming generation
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize local LLM.
        
        Args:
            config: LLM configuration with local_model_path
        """
        super().__init__(config)
        
        self.model = None
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if llama-cpp-python is installed."""
        try:
            import llama_cpp
            self.has_llama_cpp = True
        except ImportError:
            logger.error(
                "llama-cpp-python not installed. "
                "Install with: pip install llama-cpp-python"
            )
            self.has_llama_cpp = False
            raise ImportError("llama-cpp-python required for local models")
    
    def load(self) -> bool:
        """
        Load the GGUF model.
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_loaded:
            logger.info("Model already loaded")
            return True
        
        if not self.has_llama_cpp:
            logger.error("llama-cpp-python not available")
            return False
        
        model_path = Path(self.config.local_model_path)
        
        if not model_path.exists():
            logger.error(f"Model file not found: {model_path}")
            return False
        
        logger.info(f"Loading model from: {model_path}")
        
        try:
            from llama_cpp import Llama
            
            self.model = Llama(
                model_path=str(model_path),
                n_ctx=self.config.n_ctx,
                n_threads=self.config.n_threads,
                n_gpu_layers=self.config.n_gpu_layers,
                verbose=False
            )
            
            self._is_loaded = True
            logger.info("Model loaded successfully")
            
            # Log model info
            logger.info(
                f"Context window: {self.config.n_ctx}, "
                f"Threads: {self.config.n_threads}, "
                f"GPU layers: {self.config.n_gpu_layers}"
            )
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            self._is_loaded = False
            return False
    
    def unload(self) -> None:
        """Unload model and free memory."""
        if self.model is not None:
            logger.info("Unloading local model")
            del self.model
            self.model = None
            self._is_loaded = False
            
            # Force garbage collection
            import gc
            gc.collect()
    
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
            stream: Whether to stream (not used in non-streaming method)
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse with generated text
        """
        if not self._is_loaded:
            return LLMResponse(
                text="",
                error="Model not loaded. Please load the model first."
            )
        
        try:
            # Merge kwargs with config defaults
            gen_params = {
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'echo': False,
                'stop': kwargs.get('stop', []),
            }
            
            logger.debug(f"Generating with params: {gen_params}")
            
            # Generate
            output = self.model(
                prompt,
                **gen_params
            )
            
            # Extract response
            text = output['choices'][0]['text']
            
            # Build usage stats
            usage = {
                'prompt_tokens': output['usage']['prompt_tokens'],
                'completion_tokens': output['usage']['completion_tokens'],
                'total_tokens': output['usage']['total_tokens'],
            }
            
            logger.debug(f"Generated {usage['completion_tokens']} tokens")
            
            return LLMResponse(
                text=text.strip(),
                usage=usage,
                metadata={'model': 'local'}
            )
            
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return LLMResponse(
                text="",
                error=str(e)
            )
    
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
            Text chunks as they are generated
        """
        if not self._is_loaded:
            logger.error("Model not loaded")
            yield "[Error: Model not loaded]"
            return
        
        try:
            gen_params = {
                'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
                'temperature': kwargs.get('temperature', self.config.temperature),
                'top_p': kwargs.get('top_p', self.config.top_p),
                'stream': True,
                'echo': False,
                'stop': kwargs.get('stop', []),
            }
            
            logger.debug("Starting streaming generation")
            
            stream = self.model(prompt, **gen_params)
            
            for output in stream:
                chunk = output['choices'][0]['text']
                if chunk:
                    yield chunk
            
            logger.debug("Streaming generation complete")
            
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"[Error: {str(e)}]"
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        info = super().get_info()
        info.update({
            'model_path': self.config.local_model_path,
            'context_window': self.config.n_ctx,
            'threads': self.config.n_threads,
            'gpu_layers': self.config.n_gpu_layers,
        })
        return info
    
    @staticmethod
    def is_gguf_file(path: str) -> bool:
        """
        Check if file is a valid GGUF model.
        
        Args:
            path: Path to file
            
        Returns:
            True if file exists and has .gguf extension
        """
        p = Path(path)
        return p.exists() and p.suffix.lower() == '.gguf'
    
    @staticmethod
    def estimate_memory_usage(model_path: str) -> Optional[int]:
        """
        Estimate memory usage for a model.
        
        Args:
            model_path: Path to GGUF model
            
        Returns:
            Estimated memory in MB, or None if cannot estimate
        """
        try:
            size_bytes = Path(model_path).stat().st_size
            # Rough estimate: model file size + 20% overhead
            size_mb = int(size_bytes / (1024 * 1024) * 1.2)
            return size_mb
        except Exception:
            return None