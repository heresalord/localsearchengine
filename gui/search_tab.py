"""
Modern search tab with beautiful UI.
"""

import logging
from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QComboBox, QLabel, QListWidget, QListWidgetItem, QTextEdit,
    QSplitter, QGroupBox, QCheckBox, QFrame, QProgressBar
)
from PySide6.QtCore import Qt, Signal, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QFont

from .modern_styles import COLORS, get_file_type_color, get_score_color

logger = logging.getLogger(__name__)


class ModernSearchResultItem(QWidget):
    """Modern card-style search result item."""
    
    clicked = Signal(dict)
    
    def __init__(self, result: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.result = result
        self.setObjectName("resultCard")
        self._setup_ui()
        self._apply_styling()
    
    def _setup_ui(self):
        """Setup modern result card UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(10)
        
        # Header row: Icon + Title + Score badge
        header = QHBoxLayout()
        header.setSpacing(12)
        
        # File type icon and name
        file_name = self.result['metadata'].get('file_name', 'Unknown')
        file_type = self.result['metadata'].get('file_type', '').upper()
        
        # File type badge
        type_badge = QLabel(f"  {file_type}  ")
        type_badge.setStyleSheet(f"""
            background-color: {get_file_type_color(file_type)};
            color: white;
            border-radius: 6px;
            padding: 4px 10px;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 0.5px;
        """)
        header.addWidget(type_badge)
        
        # File name
        title = QLabel(file_name)
        title.setStyleSheet("""
            font-size: 15px;
            font-weight: 600;
            color: #0f172a;
        """)
        header.addWidget(title, stretch=1)
        
        # Score visualization
        score = self.result.get('score', 0.0)
        score_container = QWidget()
        score_layout = QVBoxLayout(score_container)
        score_layout.setContentsMargins(0, 0, 0, 0)
        score_layout.setSpacing(2)
        
        score_label = QLabel(f"{score*100:.0f}%")
        score_label.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 700;
            color: {get_score_color(score)};
        """)
        score_label.setAlignment(Qt.AlignRight)
        
        # Progress bar for score
        score_bar = QProgressBar()
        score_bar.setMaximum(100)
        score_bar.setValue(int(score * 100))
        score_bar.setTextVisible(False)
        score_bar.setFixedHeight(4)
        score_bar.setStyleSheet(f"""
            QProgressBar {{
                border: none;
                background-color: #e2e8f0;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {get_score_color(score)};
                border-radius: 2px;
            }}
        """)
        
        score_layout.addWidget(score_label)
        score_layout.addWidget(score_bar)
        header.addWidget(score_container)
        
        layout.addLayout(header)
        
        # Preview text
        text = self.result.get('text', '')
        preview = text[:180] + "..." if len(text) > 180 else text
        
        preview_label = QLabel(preview)
        preview_label.setWordWrap(True)
        preview_label.setStyleSheet("""
            color: #475569;
            font-size: 14px;
            line-height: 1.5;
        """)
        layout.addWidget(preview_label)
        
        # Footer: Metadata
        footer = QHBoxLayout()
        footer.setSpacing(12)
        
        chunk_info = f"Chunk {self.result['metadata'].get('chunk_index', 0) + 1} of {self.result['metadata'].get('total_chunks', 1)}"
        chunk_label = QLabel(f"📑 {chunk_info}")
        chunk_label.setStyleSheet("""
            color: #94a3b8;
            font-size: 12px;
        """)
        footer.addWidget(chunk_label)
        
        footer.addStretch()
        
        # Quick action hint
        action_hint = QLabel("Click to preview →")
        action_hint.setStyleSheet("""
            color: #a5b4fc;
            font-size: 11px;
            font-weight: 500;
        """)
        footer.addWidget(action_hint)
        
        layout.addLayout(footer)
    
    def _apply_styling(self):
        """Apply hover effects."""
        self.setStyleSheet("""
            #resultCard {
                background-color: white;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
            #resultCard:hover {
                background-color: #f8fafc;
                border-color: #a5b4fc;
            }
        """)
        self.setCursor(Qt.PointingHandCursor)
    
    def mousePressEvent(self, event):
        """Handle mouse click."""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.result)
        super().mousePressEvent(event)


class SearchTab(QWidget):
    """
    Modern search tab with enhanced UI.
    """
    
    search_completed = Signal(int)
    error_occurred = Signal(str)
    
    def __init__(self, config: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config = config
        self.current_results = []
        self.search_engine = None
        
        self._setup_ui()
        self._setup_connections()
        
        logger.info("Search tab initialized")
    
    def _setup_ui(self):
        """Setup modern UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        
        # Search header with modern design
        header = self._create_search_header()
        layout.addWidget(header)
        
        # Main content: Results + Preview
        splitter = QSplitter(Qt.Horizontal)
        
        # Results panel
        results_panel = self._create_results_panel()
        splitter.addWidget(results_panel)
        
        # Preview panel
        preview_panel = self._create_preview_panel()
        splitter.addWidget(preview_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([500, 500])
        
        layout.addWidget(splitter, stretch=1)
    
    def _create_search_header(self) -> QWidget:
        """Create modern search header."""
        container = QWidget()
        container.setObjectName("searchContainer")
        container.setStyleSheet("""
            #searchContainer {
                background-color: white;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(16)
        
        # Title
        title = QLabel("Search")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 700;
            color: #0f172a;
            letter-spacing: -0.5px;
        """)
        layout.addWidget(title)
        
        # Search input row
        input_row = QHBoxLayout()
        input_row.setSpacing(12)
        
        # Search input with icon
        search_container = QWidget()
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(16, 0, 16, 0)
        search_layout.setSpacing(12)
        
        search_icon = QLabel("🔍")
        search_icon.setStyleSheet("font-size: 18px;")
        search_layout.addWidget(search_icon)
        
        self.search_input = QLineEdit()
        self.search_input.setObjectName("searchInput")
        self.search_input.setPlaceholderText("Search your documents...")
        self.search_input.setMinimumHeight(50)
        self.search_input.setStyleSheet("""
            QLineEdit#searchInput {
                background-color: #f8fafc;
                border: 2px solid #e2e8f0;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 15px;
                color: #0f172a;
            }
            QLineEdit#searchInput:focus {
                border-color: #667eea;
                background-color: white;
            }
        """)
        search_layout.addWidget(self.search_input, stretch=1)
        
        search_container.setStyleSheet("border: none;")
        input_row.addWidget(search_container, stretch=3)
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setObjectName("searchButton")
        self.search_btn.setMinimumHeight(50)
        self.search_btn.setMinimumWidth(140)
        input_row.addWidget(self.search_btn)
        
        layout.addLayout(input_row)
        
        # Filters row
        filters_row = QHBoxLayout()
        filters_row.setSpacing(16)
        
        # File type filter
        type_label = QLabel("File Type:")
        type_label.setStyleSheet("color: #64748b; font-weight: 500;")
        filters_row.addWidget(type_label)
        
        self.file_type_combo = QComboBox()
        self.file_type_combo.addItems(["All Types", "PDF", "TXT", "MD", "DOCX", "Images"])
        self.file_type_combo.setMinimumWidth(130)
        filters_row.addWidget(self.file_type_combo)
        
        # Max results
        results_label = QLabel("Max Results:")
        results_label.setStyleSheet("color: #64748b; font-weight: 500;")
        filters_row.addWidget(results_label)
        
        self.results_count_combo = QComboBox()
        self.results_count_combo.addItems(["10", "20", "50", "100"])
        self.results_count_combo.setMinimumWidth(80)
        filters_row.addWidget(self.results_count_combo)
        
        filters_row.addStretch()
        
        # Semantic only checkbox
        self.semantic_only_check = QCheckBox("Semantic Only (Faster)")
        self.semantic_only_check.setStyleSheet("font-weight: 500;")
        filters_row.addWidget(self.semantic_only_check)
        
        layout.addLayout(filters_row)
        
        return container
    
    def _create_results_panel(self) -> QGroupBox:
        """Create results panel."""
        group = QGroupBox("Results")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # Results info header
        self.results_info = QLabel("Enter a query to search")
        self.results_info.setStyleSheet("""
            color: #64748b;
            padding: 12px;
            background-color: #f8fafc;
            border-radius: 8px;
            font-weight: 500;
        """)
        layout.addWidget(self.results_info)
        
        # Results list
        self.results_list = QListWidget()
        self.results_list.setSpacing(8)
        layout.addWidget(self.results_list)
        
        return group
    
    def _create_preview_panel(self) -> QGroupBox:
        """Create preview panel."""
        group = QGroupBox("Preview")
        layout = QVBoxLayout(group)
        layout.setSpacing(12)
        
        # File info
        self.preview_info = QLabel("Select a result to preview")
        self.preview_info.setStyleSheet("""
            color: #64748b;
            padding: 12px;
            background-color: #f8fafc;
            border-radius: 8px;
            font-weight: 500;
        """)
        self.preview_info.setWordWrap(True)
        layout.addWidget(self.preview_info)
        
        # Text preview
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet("""
            font-family: ui-monospace, 'SF Mono', Monaco, 'Cascadia Code', monospace;
            font-size: 13px;
            line-height: 1.6;
        """)
        layout.addWidget(self.preview_text)
        
        # Action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        
        self.open_file_btn = QPushButton("📂 Open File")
        self.open_file_btn.setEnabled(False)
        self.open_file_btn.setMinimumHeight(36)
        btn_row.addWidget(self.open_file_btn)
        
        self.copy_text_btn = QPushButton("📋 Copy Text")
        self.copy_text_btn.setEnabled(False)
        self.copy_text_btn.setMinimumHeight(36)
        btn_row.addWidget(self.copy_text_btn)
        
        btn_row.addStretch()
        
        layout.addLayout(btn_row)
        
        return group
    
    def _setup_connections(self):
        """Setup connections."""
        self.search_btn.clicked.connect(self._perform_search)
        self.search_input.returnPressed.connect(self._perform_search)
        self.results_list.itemClicked.connect(self._on_result_selected)
        self.open_file_btn.clicked.connect(self._open_file)
        self.copy_text_btn.clicked.connect(self._copy_text)
    
    def set_search_engine(self, engine):
        """Set search engine."""
        self.search_engine = engine
        logger.info("Search engine connected")
    
    def _perform_search(self):
        """Perform search."""
        query = self.search_input.text().strip()
        
        if not query:
            self.results_info.setText("⚠️ Please enter a search query")
            return
        
        if not self.search_engine:
            self.error_occurred.emit("Search engine not initialized")
            return
        
        logger.info(f"Searching: {query}")
        
        # UI feedback
        self.search_btn.setEnabled(False)
        self.search_btn.setText("Searching...")
        self.results_info.setText("🔍 Searching...")
        
        try:
            # Get filters
            file_type = self.file_type_combo.currentText()
            max_results = int(self.results_count_combo.currentText())
            semantic_only = self.semantic_only_check.isChecked()
            
            filters = None
            if file_type != "All Types":
                filters = {'file_type': file_type.lower()}
            
            # Search
            results = self.search_engine.search(
                query=query,
                top_k=max_results,
                filters=filters,
                semantic_only=semantic_only
            )
            
            self.current_results = results
            self._display_results(results)
            self.search_completed.emit(len(results))
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.search_btn.setEnabled(True)
            self.search_btn.setText("Search")
    
    def _display_results(self, results: List):
        """Display results with modern cards."""
        self.results_list.clear()
        
        if not results:
            self.results_info.setText("❌ No results found")
            return
        
        self.results_info.setText(f"✓ Found {len(results)} results")
        
        for result in results:
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            else:
                result_dict = result
            
            # Create modern card
            card = ModernSearchResultItem(result_dict)
            card.clicked.connect(self._on_result_clicked)
            
            item = QListWidgetItem(self.results_list)
            item.setSizeHint(card.sizeHint())
            
            self.results_list.addItem(item)
            self.results_list.setItemWidget(item, card)
    
    def _on_result_selected(self, item):
        """Handle result selection."""
        widget = self.results_list.itemWidget(item)
        if widget and hasattr(widget, 'result'):
            self._show_preview(widget.result)
    
    def _on_result_clicked(self, result: dict):
        """Handle result click."""
        self._show_preview(result)
    
    def _show_preview(self, result: dict):
        """Show preview."""
        metadata = result['metadata']
        file_name = metadata.get('file_name', 'Unknown')
        file_path = metadata.get('file_path', '')
        file_type = metadata.get('file_type', '').upper()
        
        info_html = f"""
        <div style='padding: 4px;'>
            <p style='margin: 0; font-size: 16px; font-weight: 600; color: #0f172a;'>
                📄 {file_name}
            </p>
            <p style='margin: 4px 0 0 0; font-size: 12px; color: #64748b;'>
                {file_path}
            </p>
            <p style='margin: 4px 0 0 0; font-size: 12px; color: #94a3b8;'>
                Type: {file_type} • Score: {result.get('score', 0):.3f}
            </p>
        </div>
        """
        
        self.preview_info.setText(info_html)
        self.preview_text.setText(result.get('text', ''))
        
        self.open_file_btn.setEnabled(True)
        self.copy_text_btn.setEnabled(True)
        self.current_preview = result
    
    def _open_file(self):
        """Open file."""
        if not hasattr(self, 'current_preview'):
            return
        
        file_path = self.current_preview['metadata'].get('file_path')
        if file_path:
            import os, platform
            try:
                if platform.system() == 'Windows':
                    os.startfile(file_path)
                elif platform.system() == 'Darwin':
                    os.system(f'open "{file_path}"')
                else:
                    os.system(f'xdg-open "{file_path}"')
            except Exception as e:
                self.error_occurred.emit(f"Failed to open: {e}")
    
    def _copy_text(self):
        """Copy text to clipboard."""
        from PySide6.QtWidgets import QApplication
        QApplication.clipboard().setText(self.preview_text.toPlainText())
        self.results_info.setText("✓ Text copied to clipboard!")
    
    def update_config(self, config: dict):
        """Update config."""
        self.config = config
    
    def clear_results(self):
        """Clear results."""
        self.results_list.clear()
        self.preview_text.clear()
        self.preview_info.setText("Select a result to preview")
        self.results_info.setText("Enter a query to search")
