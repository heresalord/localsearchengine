"""
Modern main window for the application.
"""

import logging
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSplitter, QStackedWidget,
    QListWidget, QListWidgetItem, QStatusBar, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont

from .search_tab import SearchTab
from .chat_tab import ChatTab
from .settings_dialog import SettingsDialog
from .modern_styles import MODERN_STYLESHEET

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Modern main application window with improved UI/UX.
    """
    
    # Signals
    settings_changed = Signal(dict)
    reindex_requested = Signal()
    
    def __init__(self, config: dict, parent: Optional[QWidget] = None):
        """Initialize main window."""
        super().__init__(parent)
        
        self.config = config
        self.current_page = 0
        
        self._setup_ui()
        self._setup_connections()
        
        logger.info("Main window initialized")
    
    def _setup_ui(self):
        """Setup the modern user interface."""
        self.setWindowTitle("Local Semantic Search Engine")
        self.setMinimumSize(1300, 850)
        
        # Apply modern stylesheet
        self.setStyleSheet(MODERN_STYLESHEET)
        
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for resizable sidebar
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Sidebar
        sidebar = self._create_sidebar()
        splitter.addWidget(sidebar)
        
        # Content area
        self.content_stack = QStackedWidget()
        self.content_stack.setContentsMargins(16, 16, 16, 16)
        splitter.addWidget(self.content_stack)
        
        # Set splitter proportions
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 5)
        splitter.setSizes([250, 1050])
        
        # Create tabs
        self._create_tabs()
        
        # Status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self._update_status("Ready")
    
    def _create_sidebar(self) -> QWidget:
        """Create the modern sidebar navigation."""
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(260)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 16)
        layout.setSpacing(20)
        
        # App title with icon
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(4)
        
        title = QLabel("🔍 Search Engine")
        title.setObjectName("appTitle")
        title_font = QFont()
        title_font.setPointSize(19)
        title_font.setBold(True)
        title_font.setLetterSpacing(QFont.AbsoluteSpacing, -0.5)
        title.setFont(title_font)
        
        subtitle = QLabel("Semantic Document Search")
        subtitle.setStyleSheet("color: #94a3b8; font-size: 12px; font-weight: 500;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(subtitle)
        layout.addWidget(title_container)
        
        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.HLine)
        divider.setStyleSheet("background-color: #334155; max-height: 1px;")
        layout.addWidget(divider)
        
        # Navigation list
        self.nav_list = QListWidget()
        self.nav_list.setObjectName("navList")
        
        # Add navigation items with icons
        search_item = QListWidgetItem("🔍  Search")
        search_item.setSizeHint(QSize(220, 48))
        self.nav_list.addItem(search_item)
        
        chat_item = QListWidgetItem("💬  Chat")
        chat_item.setSizeHint(QSize(220, 48))
        self.nav_list.addItem(chat_item)
        
        layout.addWidget(self.nav_list)
        
        # Spacer
        layout.addStretch()
        
        # Bottom buttons with modern styling
        settings_btn = QPushButton("⚙️  Settings")
        settings_btn.setObjectName("settingsButton")
        settings_btn.setMinimumHeight(44)
        settings_btn.clicked.connect(self._show_settings)
        layout.addWidget(settings_btn)
        
        about_btn = QPushButton("ℹ️  About")
        about_btn.setObjectName("aboutButton")
        about_btn.setMinimumHeight(44)
        about_btn.clicked.connect(self._show_about)
        layout.addWidget(about_btn)
        
        return sidebar
    
    def _create_tabs(self):
        """Create content tabs."""
        # Search tab
        self.search_tab = SearchTab(self.config)
        self.content_stack.addWidget(self.search_tab)
        
        # Chat tab
        self.chat_tab = ChatTab(self.config)
        self.content_stack.addWidget(self.chat_tab)
        
        # Set initial tab
        self.content_stack.setCurrentIndex(0)
        self.nav_list.setCurrentRow(0)
    
    def _setup_connections(self):
        """Setup signal/slot connections."""
        self.nav_list.currentRowChanged.connect(self._on_nav_changed)
        self.search_tab.search_completed.connect(self._on_search_completed)
        self.search_tab.error_occurred.connect(self._on_error)
        self.chat_tab.question_asked.connect(self._on_question_asked)
        self.chat_tab.error_occurred.connect(self._on_error)
    
    def _on_nav_changed(self, index: int):
        """Handle navigation change."""
        self.content_stack.setCurrentIndex(index)
        self.current_page = index
        
        page_names = ["Search", "Chat"]
        if index < len(page_names):
            self._update_status(f"Switched to {page_names[index]}")
    
    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self.config, self)
        
        if dialog.exec():
            new_config = dialog.get_config()
            self.config.update(new_config)
            self.settings_changed.emit(self.config)
            self._update_tabs_config()
            self._update_status("✓ Settings updated")
            logger.info("Settings updated")
    
    def _show_about(self):
        """Show about dialog."""
        about_text = """
        <div style='font-family: -apple-system, sans-serif; padding: 20px;'>
            <h2 style='color: #667eea; margin-bottom: 10px;'>🔍 Local Semantic Search Engine</h2>
            <p style='color: #64748b; margin: 8px 0;'><b>Version:</b> 0.1.0</p>
            <p style='line-height: 1.6; margin: 12px 0;'>
                A powerful local search engine with semantic understanding and optional AI features.
            </p>
            
            <h3 style='color: #0f172a; margin-top: 20px;'>Features:</h3>
            <ul style='line-height: 1.8; color: #475569;'>
                <li>Semantic search across documents</li>
                <li>Support for PDF, DOCX, TXT, MD, images</li>
                <li>Optional OCR for scanned documents</li>
                <li>AI-powered Q&A with local or online models</li>
                <li>Real-time file monitoring</li>
            </ul>
            
            <p style='margin-top: 20px; color: #64748b; font-size: 13px;'>
                <b>Built with:</b> Python, PySide6, ChromaDB, sentence-transformers
            </p>
        </div>
        """
        
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("About")
        msg_box.setTextFormat(Qt.RichText)
        msg_box.setText(about_text)
        msg_box.setStandardButtons(QMessageBox.Ok)
        msg_box.exec()
    
    def _update_tabs_config(self):
        """Update configuration in all tabs."""
        self.search_tab.update_config(self.config)
        self.chat_tab.update_config(self.config)
        
        llm_mode = self.config.get('llm_mode', 'none')
        chat_enabled = llm_mode != 'none'
        
        chat_item = self.nav_list.item(1)
        if chat_enabled:
            chat_item.setFlags(chat_item.flags() | Qt.ItemIsEnabled)
            chat_item.setText("💬  Chat")
        else:
            chat_item.setFlags(chat_item.flags() & ~Qt.ItemIsEnabled)
            chat_item.setText("💬  Chat (Disabled)")
    
    def _on_search_completed(self, num_results: int):
        """Handle search completion."""
        self._update_status(f"✓ Found {num_results} results")
    
    def _on_question_asked(self, question: str):
        """Handle question asked in chat."""
        self._update_status("🤔 Processing question...")
    
    def _on_error(self, error_msg: str):
        """Handle error from tabs."""
        self._update_status(f"⚠️ Error: {error_msg}")
        QMessageBox.warning(self, "Error", error_msg)
        logger.error(f"GUI error: {error_msg}")
    
    def _update_status(self, message: str, timeout: int = 3000):
        """Update status bar with modern formatting."""
        self.status_bar.showMessage(f"  {message}", timeout)
    
    def show_message(self, message: str, timeout: int = 3000):
        """Show message in status bar."""
        self._update_status(message, timeout)
    
    def set_indexing_progress(self, current: int, total: int, filename: str):
        """Update status with indexing progress."""
        percent = int((current / total) * 100) if total > 0 else 0
        self._update_status(
            f"📚 Indexing: {current}/{total} ({percent}%) - {filename}",
            0
        )
    
    def enable_chat_tab(self, enabled: bool):
        """Enable or disable chat tab."""
        chat_item = self.nav_list.item(1)
        if enabled:
            chat_item.setFlags(chat_item.flags() | Qt.ItemIsEnabled)
            chat_item.setText("💬  Chat")
        else:
            chat_item.setFlags(chat_item.flags() & ~Qt.ItemIsEnabled)
            chat_item.setText("💬  Chat (Disabled)")
            
            if self.current_page == 1:
                self.nav_list.setCurrentRow(0)
    
    def closeEvent(self, event):
        """Handle window close event."""
        logger.info("Main window closing")
        event.accept()
