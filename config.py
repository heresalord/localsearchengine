"""
Configuration management for Local Semantic Search Engine.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class Config:
    """
    Application configuration manager.
    
    Handles:
    - Loading and saving configuration
    - Default values
    - Validation
    - Configuration updates
    """
    
    DEFAULT_CONFIG = {
        # General settings
        'folder_path': '',
        'recursive': True,
        'enable_ocr': True,
        
        # Chunking settings
        'chunk_size': 800,
        'chunk_overlap': 200,
        'min_chunk_size': 50,
        
        # Embedding settings
        'embedding_model': 'BAAI/bge-small-en-v1.5',
        'device': 'cpu',  # 'cpu' or 'cuda'
        'batch_size': 50,
        
        # Search settings
        'semantic_weight': 0.7,
        'keyword_weight': 0.3,
        'min_score': 0.3,
        
        # LLM settings
        'llm_mode': 'none',  # 'none', 'local', 'api'
        
        # Local LLM settings
        'local_model_path': '',
        'n_ctx': 4096,
        'n_threads': 4,
        'n_gpu_layers': 0,
        
        # API LLM settings
        'api_provider': 'openai',  # 'openai', 'anthropic'
        'api_key': '',
        'api_model': 'gpt-3.5-turbo',
        'api_base_url': '',
        
        # Generation settings
        'temperature': 0.7,
        'max_tokens': 1000,
        'top_p': 0.9,
        'max_context_chunks': 5,
        
        # File watcher settings
        'enable_file_watcher': True,
        'debounce_seconds': 2.0,
        
        # Database settings
        'db_path': './chroma_db',
        'collection_name': 'documents',
        
        # UI settings
        'window_width': 1200,
        'window_height': 800,
        'theme': 'light',
        
        # Logging settings
        'log_level': 'INFO',
        'log_dir': './logs',
    }
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize configuration manager.
        
        Args:
            config_file: Path to configuration file
        """
        self.config_file = Path(config_file)
        self.config = self.DEFAULT_CONFIG.copy()
        
        # Load existing config if available
        if self.config_file.exists():
            self.load()
        else:
            logger.info(f"No config file found, using defaults")
            self.save()  # Save default config
    
    def load(self) -> bool:
        """
        Load configuration from file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)
            
            # Merge with defaults (in case new keys were added)
            self.config = self.DEFAULT_CONFIG.copy()
            self.config.update(loaded_config)
            
            logger.info(f"Configuration loaded from {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def save(self) -> bool:
        """
        Save configuration to file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure directory exists
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Configuration saved to {self.config_file}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        logger.debug(f"Config updated: {key} = {value}")
    
    def update(self, updates: Dict[str, Any]) -> None:
        """
        Update multiple configuration values.
        
        Args:
            updates: Dictionary of updates
        """
        self.config.update(updates)
        logger.info(f"Configuration updated with {len(updates)} values")
    
    def reset(self) -> None:
        """Reset configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        logger.info("Configuration reset to defaults")
    
    def validate(self) -> tuple[bool, list[str]]:
        """
        Validate configuration.
        
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Validate folder path
        if self.config['folder_path']:
            folder = Path(self.config['folder_path'])
            if not folder.exists():
                errors.append(f"Folder path does not exist: {self.config['folder_path']}")
            elif not folder.is_dir():
                errors.append(f"Folder path is not a directory: {self.config['folder_path']}")
        
        # Validate chunk settings
        if self.config['chunk_size'] < 100:
            errors.append("Chunk size must be at least 100")
        
        if self.config['chunk_overlap'] >= self.config['chunk_size']:
            errors.append("Chunk overlap must be less than chunk size")
        
        # Validate weights
        if not 0 <= self.config['semantic_weight'] <= 1:
            errors.append("Semantic weight must be between 0 and 1")
        
        if not 0 <= self.config['keyword_weight'] <= 1:
            errors.append("Keyword weight must be between 0 and 1")
        
        # Validate LLM settings
        if self.config['llm_mode'] == 'local':
            if not self.config['local_model_path']:
                errors.append("Local model path required for local LLM mode")
            elif not Path(self.config['local_model_path']).exists():
                errors.append(f"Local model file not found: {self.config['local_model_path']}")
        
        elif self.config['llm_mode'] == 'api':
            if not self.config['api_key']:
                errors.append("API key required for API LLM mode")
            if not self.config['api_provider']:
                errors.append("API provider required for API LLM mode")
        
        # Validate temperature
        if not 0 <= self.config['temperature'] <= 2:
            errors.append("Temperature must be between 0 and 2")
        
        is_valid = len(errors) == 0
        
        if not is_valid:
            logger.warning(f"Configuration validation failed: {errors}")
        
        return is_valid, errors
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self.config.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Get item using bracket notation."""
        return self.config[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set item using bracket notation."""
        self.config[key] = value
    
    def __contains__(self, key: str) -> bool:
        """Check if key exists."""
        return key in self.config
    
    def __repr__(self) -> str:
        """String representation."""
        return f"Config({len(self.config)} settings)"
    
    def print_config(self) -> None:
        """Print configuration in a readable format."""
        print("\n" + "=" * 60)
        print("CURRENT CONFIGURATION")
        print("=" * 60)
        
        sections = {
            'General': ['folder_path', 'recursive', 'enable_ocr'],
            'Chunking': ['chunk_size', 'chunk_overlap', 'min_chunk_size'],
            'Embeddings': ['embedding_model', 'device', 'batch_size'],
            'Search': ['semantic_weight', 'keyword_weight', 'min_score'],
            'LLM': ['llm_mode', 'local_model_path', 'api_provider', 'api_model'],
            'Generation': ['temperature', 'max_tokens', 'max_context_chunks'],
            'Database': ['db_path', 'collection_name'],
        }
        
        for section, keys in sections.items():
            print(f"\n{section}:")
            for key in keys:
                if key in self.config:
                    value = self.config[key]
                    # Mask sensitive data
                    if 'key' in key.lower() and value:
                        value = '*' * 8
                    print(f"  {key}: {value}")
        
        print("\n" + "=" * 60 + "\n")


# Singleton instance
_config_instance: Optional[Config] = None


def get_config(config_file: str = 'config.json') -> Config:
    """
    Get the global configuration instance.
    
    Args:
        config_file: Path to configuration file
        
    Returns:
        Config instance
    """
    global _config_instance
    
    if _config_instance is None:
        _config_instance = Config(config_file)
    
    return _config_instance


# Example usage
if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Create config
    config = Config('test_config.json')
    
    # Print default config
    config.print_config()
    
    # Update some values
    config.update({
        'folder_path': '/path/to/documents',
        'llm_mode': 'local',
        'local_model_path': '/path/to/model.gguf',
        'temperature': 0.8,
    })
    
    # Validate
    is_valid, errors = config.validate()
    if not is_valid:
        print("\nValidation errors:")
        for error in errors:
            print(f"  - {error}")
    
    # Save
    config.save()
    
    print("\nConfiguration saved to test_config.json")