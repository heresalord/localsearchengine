"""
GUI module for Local Semantic Search Engine.

This module provides the PySide6-based user interface with:
- Main window with sidebar navigation
- Search tab for document retrieval
- Chat tab for AI-powered Q&A (optional)
- Settings dialog for configuration
"""

from .main_window import MainWindow
from .search_tab import SearchTab
from .chat_tab import ChatTab
from .settings_dialog import SettingsDialog

__all__ = [
    'MainWindow',
    'SearchTab',
    'ChatTab',
    'SettingsDialog',
]

__version__ = '0.1.0'