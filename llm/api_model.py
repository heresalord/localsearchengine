"""
API-based LLM implementation (OpenAI, Anthropic, etc.).
"""

import logging
from typing import Iterator, Dict, Any, Optional

from .base import BaseLLM, LLMConfig, LLMResponse

logger = logging.getLogger(__name__)


class APILLM(BaseLLM):
    """
    API-based LLM using cloud providers.
    
    Supports:
    - OpenAI (GPT-3.5, GPT-4)
    - Anthropic (Claude)
    - Custom endpoints (OpenAI-compatible APIs)
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize API LLM.
        
        Args:
            config: LLM configuration with API settings
        """
        super().__init__(config)
        
        self.client = None
        self.provider = config.api_provider.lower()
        
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check if required API libraries are installed."""
        self.has_openai = False
        self.has_anthropic = False
        
        if self.provider == "openai":
            try:
                import openai
                self.has_openai = True
            except ImportError:
                logger.error("openai package not installed. Install with: pip install openai")
                raise ImportError("openai package required for OpenAI API")
        
        elif self.provider == "anthropic":
            try:
                import anthropic
                self.has_anthropic = True
            except ImportError:
                logger.error("anthropic package not installed. Install with: pip install anthropic")
                raise ImportError("anthropic package required for Anthropic API")
    
    def load(self) -> bool:
        """
        Initialize API client.
        
        Returns:
            True if successful, False otherwise
        """
        if self._is_loaded:
            logger.info("API client already initialized")
            return True
        
        try:
            if self.provider == "openai":
                self._init_openai()
            elif self.provider == "anthropic":
                self._init_anthropic()
            else:
                logger.error(f"Unsupported API provider: {self.provider}")
                return False
            
            self._is_loaded = True
            logger.info(f"API client initialized for {self.provider}")
            return True
            
        except Exception as e:
            logger.error(f"Error initializing API client: {e}")
            return False
    
    def _init_openai(self):
        """Initialize OpenAI client."""
        from openai import OpenAI
        
        kwargs = {'api_key': self.config.api_key}
        
        if self.config.api_base_url:
            kwargs['base_url'] = self.config.api_base_url
        
        self.client = OpenAI(**kwargs)
        logger.info(f"OpenAI client initialized (model: {self.config.api_model})")
    
    def _init_anthropic(self):
        """Initialize Anthropic client."""
        from anthropic import Anthropic
        
        self.client = Anthropic(api_key=self.config.api_key)
        logger.info(f"Anthropic client initialized (model: {self.config.api_model})")
    
    def unload(self) -> None:
        """Clean up API client."""
        if self.client is not None:
            logger.info("Cleaning up API client")
            self.client = None
            self._is_loaded = False
    
    def generate(
        self,
        prompt: str,
        stream: bool = False,
        **kwargs
    ) -> LLMResponse:
        """
        Generate text using API.
        
        Args:
            prompt: Input prompt
            stream: Whether to stream (not used here)
            **kwargs: Additional generation parameters
            
        Returns:
            LLMResponse with generated text
        """
        if not self._is_loaded:
            return LLMResponse(
                text="",
                error="API client not initialized. Please load first."
            )
        
        try:
            if self.provider == "openai":
                return self._generate_openai(prompt, **kwargs)
            elif self.provider == "anthropic":
                return self._generate_anthropic(prompt, **kwargs)
            else:
                return LLMResponse(
                    text="",
                    error=f"Unsupported provider: {self.provider}"
                )
                
        except Exception as e:
            logger.error(f"Error generating text: {e}")
            return LLMResponse(
                text="",
                error=str(e)
            )
    
    def _generate_openai(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using OpenAI API."""
        params = {
            'model': kwargs.get('model', self.config.api_model),
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'top_p': kwargs.get('top_p', self.config.top_p),
        }
        
        logger.debug(f"Calling OpenAI API with model: {params['model']}")
        
        response = self.client.chat.completions.create(**params)
        
        text = response.choices[0].message.content
        
        usage = {
            'prompt_tokens': response.usage.prompt_tokens,
            'completion_tokens': response.usage.completion_tokens,
            'total_tokens': response.usage.total_tokens,
        }
        
        logger.debug(f"OpenAI response: {usage['total_tokens']} tokens")
        
        return LLMResponse(
            text=text.strip(),
            usage=usage,
            metadata={
                'provider': 'openai',
                'model': params['model'],
                'finish_reason': response.choices[0].finish_reason
            }
        )
    
    def _generate_anthropic(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate using Anthropic API."""
        params = {
            'model': kwargs.get('model', self.config.api_model),
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'top_p': kwargs.get('top_p', self.config.top_p),
        }
        
        logger.debug(f"Calling Anthropic API with model: {params['model']}")
        
        response = self.client.messages.create(**params)
        
        text = response.content[0].text
        
        usage = {
            'prompt_tokens': response.usage.input_tokens,
            'completion_tokens': response.usage.output_tokens,
            'total_tokens': response.usage.input_tokens + response.usage.output_tokens,
        }
        
        logger.debug(f"Anthropic response: {usage['total_tokens']} tokens")
        
        return LLMResponse(
            text=text.strip(),
            usage=usage,
            metadata={
                'provider': 'anthropic',
                'model': params['model'],
                'stop_reason': response.stop_reason
            }
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
            logger.error("API client not initialized")
            yield "[Error: API client not initialized]"
            return
        
        try:
            if self.provider == "openai":
                yield from self._stream_openai(prompt, **kwargs)
            elif self.provider == "anthropic":
                yield from self._stream_anthropic(prompt, **kwargs)
            else:
                yield f"[Error: Unsupported provider: {self.provider}]"
                
        except Exception as e:
            logger.error(f"Error in streaming generation: {e}")
            yield f"[Error: {str(e)}]"
    
    def _stream_openai(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream using OpenAI API."""
        params = {
            'model': kwargs.get('model', self.config.api_model),
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'stream': True,
        }
        
        logger.debug("Starting OpenAI streaming")
        
        stream = self.client.chat.completions.create(**params)
        
        for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    def _stream_anthropic(self, prompt: str, **kwargs) -> Iterator[str]:
        """Stream using Anthropic API."""
        params = {
            'model': kwargs.get('model', self.config.api_model),
            'messages': [{'role': 'user', 'content': prompt}],
            'max_tokens': kwargs.get('max_tokens', self.config.max_tokens),
            'temperature': kwargs.get('temperature', self.config.temperature),
            'stream': True,
        }
        
        logger.debug("Starting Anthropic streaming")
        
        with self.client.messages.stream(**params) as stream:
            for text in stream.text_stream:
                yield text
    
    def get_info(self) -> Dict[str, Any]:
        """Get API information."""
        info = super().get_info()
        info.update({
            'provider': self.provider,
            'model': self.config.api_model,
            'has_api_key': bool(self.config.api_key),
        })
        return info
    
    @staticmethod
    def get_available_providers() -> list:
        """Get list of supported API providers."""
        return ['openai', 'anthropic']
    
    @staticmethod
    def get_default_models(provider: str) -> list:
        """
        Get default model options for a provider.
        
        Args:
            provider: API provider name
            
        Returns:
            List of model names
        """
        models = {
            'openai': [
                'gpt-4',
                'gpt-4-turbo-preview',
                'gpt-3.5-turbo',
                'gpt-3.5-turbo-16k',
            ],
            'anthropic': [
                'claude-3-opus-20240229',
                'claude-3-sonnet-20240229',
                'claude-3-haiku-20240307',
                'claude-2.1',
            ],
        }
        
        return models.get(provider.lower(), [])