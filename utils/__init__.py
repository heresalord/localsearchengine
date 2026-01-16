"""
Utilities module for Local Semantic Search Engine.

This module provides utility functions and classes for:
- File system monitoring
- Logging configuration
- Helper functions
"""

from .file_watcher import FileWatcher
from .logger import setup_logger, get_logger, configure_third_party_loggers

__all__ = [
    'FileWatcher',
    'setup_logger',
    'get_logger',
    'configure_third_party_loggers',
]

__version__ = '0.1.0'