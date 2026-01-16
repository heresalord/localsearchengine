"""
Local Semantic Search Engine - Main Entry Point

A powerful desktop application for semantic search across documents
with optional AI-powered Q&A capabilities.
"""

import sys
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication, QMessageBox
from PySide6.QtCore import QThread, Signal

# Import core modules
from core import (
    EmbeddingGenerator,
    VectorStore,
    FileLoader,
    TextChunker,
    DocumentIndexer,
    SearchEngine
)

# Import LLM modules
from llm import create_llm, LLMConfig

# Import GUI modules
from gui import MainWindow

# Import utilities
from utils import FileWatcher, setup_logger, configure_third_party_loggers

# Import configuration
from config import get_config


class ApplicationController:
    """
    Main application controller.
    
    Coordinates between:
    - Core components (indexer, search engine)
    - LLM (optional)
    - GUI
    - File watcher
    """
    
    def __init__(self, config_file: str = 'config.json'):
        """
        Initialize application controller.
        
        Args:
            config_file: Path to configuration file
        """
        # Load configuration
        self.config = get_config(config_file)
        
        # Setup logging
        log_level = getattr(logging, self.config['log_level'].upper(), logging.INFO)
        self.logger = setup_logger(
            name='search_engine',
            level=log_level,
            log_dir=self.config['log_dir']
        )
        
        # Suppress verbose third-party logs
        configure_third_party_loggers(logging.WARNING)
        
        self.logger.info("=" * 80)
        self.logger.info("LOCAL SEMANTIC SEARCH ENGINE - STARTING")
        self.logger.info("=" * 80)
        
        # Initialize components
        self.embedder: Optional[EmbeddingGenerator] = None
        self.vector_store: Optional[VectorStore] = None
        self.file_loader: Optional[FileLoader] = None
        self.chunker: Optional[TextChunker] = None
        self.indexer: Optional[DocumentIndexer] = None
        self.search_engine: Optional[SearchEngine] = None
        self.llm: Optional[any] = None
        self.file_watcher: Optional[FileWatcher] = None
        
        # GUI
        self.main_window: Optional[MainWindow] = None
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize all components."""
        try:
            self.logger.info("Initializing core components...")
            
            # Embeddings
            self.embedder = EmbeddingGenerator(
                model_name=self.config['embedding_model'],
                device=self.config['device']
            )
            
            # Vector store
            self.vector_store = VectorStore(
                persist_directory=self.config['db_path'],
                collection_name=self.config['collection_name']
            )
            
            # File loader
            self.file_loader = FileLoader(
                enable_ocr=self.config['enable_ocr']
            )
            
            # Chunker
            self.chunker = TextChunker(
                chunk_size=self.config['chunk_size'],
                chunk_overlap=self.config['chunk_overlap'],
                min_chunk_size=self.config['min_chunk_size']
            )
            
            # Indexer
            self.indexer = DocumentIndexer(
                file_loader=self.file_loader,
                chunker=self.chunker,
                embedder=self.embedder,
                vector_store=self.vector_store,
                batch_size=self.config['batch_size']
            )
            
            # Search engine
            self.search_engine = SearchEngine(
                embedder=self.embedder,
                vector_store=self.vector_store,
                semantic_weight=self.config['semantic_weight'],
                keyword_weight=self.config['keyword_weight'],
                min_score=self.config['min_score']
            )
            
            self.logger.info("Core components initialized successfully")
            
            # Initialize LLM if configured
            self._initialize_llm()
            
            # Initialize file watcher if enabled
            if self.config['enable_file_watcher'] and self.config['folder_path']:
                self._initialize_file_watcher()
            
        except Exception as e:
            self.logger.exception(f"Error initializing components: {e}")
            raise
    
    def _initialize_llm(self):
        """Initialize LLM based on configuration."""
        llm_mode = self.config['llm_mode']
        
        if llm_mode == 'none':
            self.logger.info("LLM disabled (mode: none)")
            return
        
        try:
            self.logger.info(f"Initializing LLM (mode: {llm_mode})...")
            
            llm_config = LLMConfig(
                mode=llm_mode,
                local_model_path=self.config.get('local_model_path'),
                n_ctx=self.config.get('n_ctx', 4096),
                n_threads=self.config.get('n_threads', 4),
                n_gpu_layers=self.config.get('n_gpu_layers', 0),
                api_provider=self.config.get('api_provider'),
                api_key=self.config.get('api_key'),
                api_model=self.config.get('api_model'),
                api_base_url=self.config.get('api_base_url'),
                temperature=self.config.get('temperature', 0.7),
                max_tokens=self.config.get('max_tokens', 1000),
                top_p=self.config.get('top_p', 0.9),
                max_context_chunks=self.config.get('max_context_chunks', 5)
            )
            
            self.llm = create_llm(llm_config)
            
            if self.llm.load():
                self.logger.info("LLM initialized successfully")
            else:
                self.logger.error("Failed to load LLM")
                self.llm = None
                
        except Exception as e:
            self.logger.exception(f"Error initializing LLM: {e}")
            self.llm = None
    
    def _initialize_file_watcher(self):
        """Initialize file system watcher."""
        try:
            folder_path = self.config['folder_path']
            
            if not folder_path or not Path(folder_path).exists():
                self.logger.warning("Cannot start file watcher: invalid folder path")
                return
            
            self.logger.info(f"Initializing file watcher for: {folder_path}")
            
            self.file_watcher = FileWatcher(
                directory=folder_path,
                supported_extensions=set(FileLoader.get_supported_extensions()),
                on_created=self._on_file_created,
                on_modified=self._on_file_modified,
                on_deleted=self._on_file_deleted,
                recursive=self.config['recursive'],
                debounce_seconds=self.config['debounce_seconds']
            )
            
            self.file_watcher.start()
            self.logger.info("File watcher started")
            
        except Exception as e:
            self.logger.exception(f"Error initializing file watcher: {e}")
            self.file_watcher = None
    
    def _on_file_created(self, file_path: str):
        """Handle file creation."""
        self.logger.info(f"File created, indexing: {file_path}")
        try:
            self.indexer.index_file(file_path)
        except Exception as e:
            self.logger.error(f"Error indexing new file: {e}")
    
    def _on_file_modified(self, file_path: str):
        """Handle file modification."""
        self.logger.info(f"File modified, re-indexing: {file_path}")
        try:
            self.indexer.index_file(file_path)
        except Exception as e:
            self.logger.error(f"Error re-indexing modified file: {e}")
    
    def _on_file_deleted(self, file_path: str):
        """Handle file deletion."""
        self.logger.info(f"File deleted, removing from index: {file_path}")
        try:
            results = self.vector_store.get_by_filter({'file_path': file_path})
            if results['ids']:
                self.vector_store.delete_documents(results['ids'])
        except Exception as e:
            self.logger.error(f"Error removing deleted file from index: {e}")
    
    def run(self):
        """Run the application."""
        try:
            # Create Qt application
            app = QApplication(sys.argv)
            app.setApplicationName("Local Semantic Search Engine")
            app.setOrganizationName("SearchEngine")
            
            # Create main window
            self.main_window = MainWindow(self.config.to_dict())
            
            # Connect components to GUI
            self.main_window.search_tab.set_search_engine(self.search_engine)
            
            if self.llm:
                self.main_window.chat_tab.set_llm(self.llm)
                self.main_window.chat_tab.set_search_engine(self.search_engine)
                self.main_window.enable_chat_tab(True)
            else:
                self.main_window.enable_chat_tab(False)
            
            # Connect signals
            self.main_window.settings_changed.connect(self._on_settings_changed)
            
            # Show window
            self.main_window.show()
            
            # Check if initial indexing is needed
            self._check_initial_indexing()
            
            self.logger.info("Application started successfully")
            
            # Run application
            exit_code = app.exec()
            
            # Cleanup
            self._cleanup()
            
            return exit_code
            
        except Exception as e:
            self.logger.exception(f"Fatal error: {e}")
            return 1
    
    def _check_initial_indexing(self):
        """Check if initial indexing is needed."""
        doc_count = self.vector_store.count()
        folder_path = self.config['folder_path']
        
        if doc_count == 0 and folder_path and Path(folder_path).exists():
            reply = QMessageBox.question(
                self.main_window,
                "Initial Indexing",
                f"No documents found in database.\n\n"
                f"Would you like to index documents in:\n{folder_path}?",
                QMessageBox.Yes | QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self._start_indexing(folder_path)
    
    def _start_indexing(self, folder_path: str):
        """Start indexing in background."""
        self.logger.info(f"Starting indexing of: {folder_path}")
        
        def progress_callback(current, total, filename):
            if self.main_window:
                self.main_window.set_indexing_progress(current, total, filename)
        
        # Run in thread (simplified - in production, use QThread properly)
        try:
            stats = self.indexer.index_directory(
                directory=folder_path,
                recursive=self.config['recursive'],
                progress_callback=progress_callback
            )
            
            if self.main_window:
                self.main_window.show_message(
                    f"Indexing complete: {stats['indexed_files']} files indexed "
                    f"({stats['total_chunks']} chunks) in {stats['duration']:.1f}s",
                    5000
                )
            
            self.logger.info(f"Indexing complete: {stats}")
            
        except Exception as e:
            self.logger.exception(f"Error during indexing: {e}")
            if self.main_window:
                QMessageBox.critical(
                    self.main_window,
                    "Indexing Error",
                    f"An error occurred during indexing:\n{str(e)}"
                )
    
    def _on_settings_changed(self, new_config: dict):
        """Handle settings changes."""
        self.logger.info("Settings changed, updating configuration...")
        
        # Update config
        self.config.update(new_config)
        self.config.save()
        
        # Handle special flags
        if new_config.get('reset_database'):
            self._reset_database()
        
        if new_config.get('trigger_reindex'):
            folder_path = self.config['folder_path']
            if folder_path:
                self._start_indexing(folder_path)
        
        # Reinitialize LLM if mode changed
        if self.config['llm_mode'] != new_config.get('llm_mode'):
            if self.llm:
                self.llm.unload()
            self._initialize_llm()
            
            if self.main_window:
                if self.llm:
                    self.main_window.chat_tab.set_llm(self.llm)
                    self.main_window.enable_chat_tab(True)
                else:
                    self.main_window.enable_chat_tab(False)
        
        # Update file watcher
        try:
            if self.config['enable_file_watcher'] and self.config['folder_path']:
                if self.file_watcher:
                    try:
                        self.file_watcher.update_directory(self.config['folder_path'])
                    except Exception as e:
                        self.logger.error(f"Error updating file watcher: {e}")
                        # Recreate file watcher from scratch
                        self.file_watcher.stop()
                        self.file_watcher = None
                        self._initialize_file_watcher()
                else:
                    self._initialize_file_watcher()
            elif self.file_watcher:
                self.file_watcher.stop()
                self.file_watcher = None
        except Exception as e:
            self.logger.error(f"Error managing file watcher: {e}")
    
    def _reset_database(self):
        """Reset the vector database."""
        self.logger.warning("Resetting database...")
        try:
            self.vector_store.reset()
            self.logger.info("Database reset complete")
            
            if self.main_window:
                self.main_window.show_message("Database reset complete", 3000)
                
        except Exception as e:
            self.logger.exception(f"Error resetting database: {e}")
    
    def _cleanup(self):
        """Clean up resources."""
        self.logger.info("Cleaning up resources...")
        
        # Stop file watcher
        if self.file_watcher:
            self.file_watcher.stop()
        
        # Unload LLM
        if self.llm:
            self.llm.unload()
        
        # Unload embedder
        if self.embedder:
            self.embedder.unload_model()
        
        self.logger.info("Cleanup complete")
        self.logger.info("=" * 80)
        self.logger.info("APPLICATION SHUTDOWN")
        self.logger.info("=" * 80)


def main():
    """Main entry point."""
    try:
        controller = ApplicationController()
        return controller.run()
    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        logging.exception("Fatal error")
        return 1


if __name__ == '__main__':
    sys.exit(main())