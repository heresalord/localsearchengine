"""
Settings dialog for application configuration.
"""

import logging
from pathlib import Path
from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLineEdit, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QLabel, QFileDialog, QGroupBox,
    QDialogButtonBox, QTabWidget, QWidget, QMessageBox
)
from PySide6.QtCore import Qt

logger = logging.getLogger(__name__)


class SettingsDialog(QDialog):
    """
    Settings dialog for configuration.
    
    Sections:
    - General: Folder selection, indexing options
    - LLM: Model configuration
    - Advanced: Performance settings
    """
    
    def __init__(self, config: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config = config.copy()  # Work with a copy
        
        self._setup_ui()
        self._load_config()
        
        logger.info("Settings dialog opened")
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setWindowTitle("Settings")
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)
        
        layout = QVBoxLayout(self)
        
        # Tab widget for different sections
        tabs = QTabWidget()
        
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_llm_tab(), "LLM")
        tabs.addTab(self._create_advanced_tab(), "Advanced")
        
        layout.addWidget(tabs)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Apply).clicked.connect(self._apply_settings)
        
        layout.addWidget(button_box)
    
    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Folder selection
        folder_group = QGroupBox("Document Folder")
        folder_layout = QVBoxLayout(folder_group)
        
        folder_row = QHBoxLayout()
        self.folder_input = QLineEdit()
        self.folder_input.setPlaceholderText("Select folder to index...")
        folder_row.addWidget(self.folder_input)
        
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_folder)
        folder_row.addWidget(browse_btn)
        
        folder_layout.addLayout(folder_row)
        
        self.recursive_check = QCheckBox("Include subfolders (recursive)")
        self.recursive_check.setChecked(True)
        folder_layout.addWidget(self.recursive_check)
        
        layout.addWidget(folder_group)
        
        # Indexing options
        index_group = QGroupBox("Indexing Options")
        index_layout = QFormLayout(index_group)
        
        self.ocr_check = QCheckBox()
        self.ocr_check.setChecked(True)
        index_layout.addRow("Enable OCR:", self.ocr_check)
        
        self.chunk_size_spin = QSpinBox()
        self.chunk_size_spin.setRange(200, 2000)
        self.chunk_size_spin.setSingleStep(100)
        self.chunk_size_spin.setValue(800)
        self.chunk_size_spin.setSuffix(" chars")
        index_layout.addRow("Chunk Size:", self.chunk_size_spin)
        
        self.chunk_overlap_spin = QSpinBox()
        self.chunk_overlap_spin.setRange(0, 500)
        self.chunk_overlap_spin.setSingleStep(50)
        self.chunk_overlap_spin.setValue(200)
        self.chunk_overlap_spin.setSuffix(" chars")
        index_layout.addRow("Chunk Overlap:", self.chunk_overlap_spin)
        
        layout.addWidget(index_group)
        
        # Re-index button
        reindex_btn = QPushButton("🔄 Re-Index All Documents")
        reindex_btn.setMinimumHeight(40)
        reindex_btn.clicked.connect(self._trigger_reindex)
        layout.addWidget(reindex_btn)
        
        layout.addStretch()
        
        return widget
    
    def _create_llm_tab(self) -> QWidget:
        """Create LLM settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # LLM mode selection
        mode_group = QGroupBox("LLM Mode")
        mode_layout = QVBoxLayout(mode_group)
        
        mode_info = QLabel(
            "Select how you want to use AI features:\n"
            "• None: Pure search only\n"
            "• Local: Use local GGUF model (private, no internet)\n"
            "• API: Use online service (requires API key)"
        )
        mode_info.setWordWrap(True)
        mode_info.setStyleSheet("color: #555; padding: 10px; background: #f9f9f9;")
        mode_layout.addWidget(mode_info)
        
        self.llm_mode_combo = QComboBox()
        self.llm_mode_combo.addItems(["None", "Local", "API"])
        self.llm_mode_combo.currentTextChanged.connect(self._on_llm_mode_changed)
        mode_layout.addWidget(self.llm_mode_combo)
        
        layout.addWidget(mode_group)
        
        # Local model settings
        self.local_group = QGroupBox("Local Model Settings")
        local_layout = QFormLayout(self.local_group)
        
        model_row = QHBoxLayout()
        self.model_path_input = QLineEdit()
        self.model_path_input.setPlaceholderText("Path to .gguf model file...")
        model_row.addWidget(self.model_path_input)
        
        model_browse_btn = QPushButton("Browse...")
        model_browse_btn.clicked.connect(self._browse_model)
        model_row.addWidget(model_browse_btn)
        
        local_layout.addRow("Model Path:", model_row)
        
        self.gpu_layers_spin = QSpinBox()
        self.gpu_layers_spin.setRange(0, 100)
        self.gpu_layers_spin.setValue(0)
        self.gpu_layers_spin.setToolTip("Number of layers to offload to GPU (0 = CPU only)")
        local_layout.addRow("GPU Layers:", self.gpu_layers_spin)
        
        layout.addWidget(self.local_group)
        
        # API settings
        self.api_group = QGroupBox("API Settings")
        api_layout = QFormLayout(self.api_group)
        
        self.api_provider_combo = QComboBox()
        self.api_provider_combo.addItems(["OpenAI", "Anthropic"])
        self.api_provider_combo.currentTextChanged.connect(self._on_api_provider_changed)
        api_layout.addRow("Provider:", self.api_provider_combo)
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("Enter API key...")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_layout.addRow("API Key:", self.api_key_input)
        
        self.api_model_combo = QComboBox()
        api_layout.addRow("Model:", self.api_model_combo)
        
        layout.addWidget(self.api_group)
        
        # Generation settings
        gen_group = QGroupBox("Generation Settings")
        gen_layout = QFormLayout(gen_group)
        
        self.temperature_spin = QSpinBox()
        self.temperature_spin.setRange(0, 100)
        self.temperature_spin.setValue(70)
        self.temperature_spin.setSuffix(" %")
        gen_layout.addRow("Temperature:", self.temperature_spin)
        
        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(100, 4000)
        self.max_tokens_spin.setSingleStep(100)
        self.max_tokens_spin.setValue(1000)
        gen_layout.addRow("Max Tokens:", self.max_tokens_spin)
        
        layout.addWidget(gen_group)
        
        layout.addStretch()
        
        # Initialize visibility
        self._on_llm_mode_changed(self.llm_mode_combo.currentText())
        
        return widget
    
    def _create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Search settings
        search_group = QGroupBox("Search Settings")
        search_layout = QFormLayout(search_group)
        
        self.semantic_weight_spin = QSpinBox()
        self.semantic_weight_spin.setRange(0, 100)
        self.semantic_weight_spin.setValue(70)
        self.semantic_weight_spin.setSuffix(" %")
        search_layout.addRow("Semantic Weight:", self.semantic_weight_spin)
        
        self.keyword_weight_spin = QSpinBox()
        self.keyword_weight_spin.setRange(0, 100)
        self.keyword_weight_spin.setValue(30)
        self.keyword_weight_spin.setSuffix(" %")
        search_layout.addRow("Keyword Weight:", self.keyword_weight_spin)
        
        layout.addWidget(search_group)
        
        # Performance settings
        perf_group = QGroupBox("Performance")
        perf_layout = QFormLayout(perf_group)
        
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(10, 100)
        self.batch_size_spin.setSingleStep(10)
        self.batch_size_spin.setValue(50)
        perf_layout.addRow("Batch Size:", self.batch_size_spin)
        
        self.embedding_device_combo = QComboBox()
        self.embedding_device_combo.addItems(["CPU", "CUDA"])
        perf_layout.addRow("Embedding Device:", self.embedding_device_combo)
        
        layout.addWidget(perf_group)
        
        # Database settings
        db_group = QGroupBox("Database")
        db_layout = QVBoxLayout(db_group)
        
        db_info = QLabel(f"ChromaDB Location: ./chroma_db")
        db_layout.addWidget(db_info)
        
        reset_btn = QPushButton("⚠️ Reset Database (Delete All)")
        reset_btn.clicked.connect(self._reset_database)
        reset_btn.setStyleSheet("background-color: #e74c3c; color: white;")
        db_layout.addWidget(reset_btn)
        
        layout.addWidget(db_group)
        
        layout.addStretch()
        
        return widget
    
    def _load_config(self):
        """Load configuration into UI."""
        # General
        self.folder_input.setText(self.config.get('folder_path', ''))
        self.recursive_check.setChecked(self.config.get('recursive', True))
        self.ocr_check.setChecked(self.config.get('enable_ocr', True))
        self.chunk_size_spin.setValue(self.config.get('chunk_size', 800))
        self.chunk_overlap_spin.setValue(self.config.get('chunk_overlap', 200))
        
        # LLM
        llm_mode = self.config.get('llm_mode', 'none')
        mode_map = {'none': 'None', 'local': 'Local', 'api': 'API'}
        self.llm_mode_combo.setCurrentText(mode_map.get(llm_mode, 'None'))
        
        self.model_path_input.setText(self.config.get('local_model_path', ''))
        self.gpu_layers_spin.setValue(self.config.get('n_gpu_layers', 0))
        
        api_provider = self.config.get('api_provider', 'openai')
        self.api_provider_combo.setCurrentText(api_provider.capitalize())
        self.api_key_input.setText(self.config.get('api_key', ''))
        
        self.temperature_spin.setValue(int(self.config.get('temperature', 0.7) * 100))
        self.max_tokens_spin.setValue(self.config.get('max_tokens', 1000))
        
        # Advanced
        self.semantic_weight_spin.setValue(int(self.config.get('semantic_weight', 0.7) * 100))
        self.keyword_weight_spin.setValue(int(self.config.get('keyword_weight', 0.3) * 100))
        self.batch_size_spin.setValue(self.config.get('batch_size', 50))
        
        device = self.config.get('device', 'cpu')
        self.embedding_device_combo.setCurrentText(device.upper())
    
    def _browse_folder(self):
        """Browse for document folder."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Document Folder",
            self.folder_input.text() or str(Path.home())
        )
        
        if folder:
            self.folder_input.setText(folder)
    
    def _browse_model(self):
        """Browse for GGUF model file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select GGUF Model",
            self.model_path_input.text() or str(Path.home()),
            "GGUF Models (*.gguf);;All Files (*)"
        )
        
        if file_path:
            self.model_path_input.setText(file_path)
    
    def _on_llm_mode_changed(self, mode: str):
        """Handle LLM mode change."""
        self.local_group.setVisible(mode == "Local")
        self.api_group.setVisible(mode == "API")
    
    def _on_api_provider_changed(self, provider: str):
        """Handle API provider change."""
        self.api_model_combo.clear()
        
        if provider == "OpenAI":
            models = ["gpt-3.5-turbo", "gpt-4", "gpt-4-turbo-preview"]
        elif provider == "Anthropic":
            models = ["claude-3-sonnet-20240229", "claude-3-opus-20240229", "claude-3-haiku-20240307"]
        else:
            models = []
        
        self.api_model_combo.addItems(models)
    
    def _trigger_reindex(self):
        """Trigger re-indexing."""
        reply = QMessageBox.question(
            self,
            "Re-Index",
            "This will re-index all documents in the selected folder. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            QMessageBox.information(
                self,
                "Re-Index",
                "Re-indexing will start when you close settings."
            )
            self.config['trigger_reindex'] = True
    
    def _reset_database(self):
        """Reset the vector database."""
        reply = QMessageBox.warning(
            self,
            "Reset Database",
            "This will delete ALL indexed documents. This cannot be undone. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config['reset_database'] = True
            QMessageBox.information(
                self,
                "Reset Database",
                "Database will be reset when you close settings."
            )
    
    def _apply_settings(self):
        """Apply settings without closing."""
        self._save_config()
        QMessageBox.information(self, "Settings", "Settings applied successfully!")
    
    def _save_config(self):
        """Save UI values to config."""
        # General
        self.config['folder_path'] = self.folder_input.text()
        self.config['recursive'] = self.recursive_check.isChecked()
        self.config['enable_ocr'] = self.ocr_check.isChecked()
        self.config['chunk_size'] = self.chunk_size_spin.value()
        self.config['chunk_overlap'] = self.chunk_overlap_spin.value()
        
        # LLM
        mode_map = {'None': 'none', 'Local': 'local', 'API': 'api'}
        self.config['llm_mode'] = mode_map[self.llm_mode_combo.currentText()]
        
        self.config['local_model_path'] = self.model_path_input.text()
        self.config['n_gpu_layers'] = self.gpu_layers_spin.value()
        
        self.config['api_provider'] = self.api_provider_combo.currentText().lower()
        self.config['api_key'] = self.api_key_input.text()
        self.config['api_model'] = self.api_model_combo.currentText()
        
        self.config['temperature'] = self.temperature_spin.value() / 100.0
        self.config['max_tokens'] = self.max_tokens_spin.value()
        
        # Advanced
        self.config['semantic_weight'] = self.semantic_weight_spin.value() / 100.0
        self.config['keyword_weight'] = self.keyword_weight_spin.value() / 100.0
        self.config['batch_size'] = self.batch_size_spin.value()
        self.config['device'] = self.embedding_device_combo.currentText().lower()
    
    def get_config(self) -> dict:
        """
        Get the updated configuration.
        
        Returns:
            Configuration dictionary
        """
        self._save_config()
        return self.config
    
    def accept(self):
        """Handle dialog acceptance."""
        self._save_config()
        super().accept()