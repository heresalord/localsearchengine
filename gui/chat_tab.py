"""
Chat tab for AI-powered Q&A over documents.
"""

import logging
from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit,
    QPushButton, QLabel, QScrollArea, QFrame, QGroupBox
)
from PySide6.QtCore import Qt, Signal, QThread
from PySide6.QtGui import QFont, QTextCursor

logger = logging.getLogger(__name__)


class ChatMessage(QFrame):
    """Widget for a single chat message."""
    
    def __init__(self, text: str, is_user: bool, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.is_user = is_user
        self._setup_ui(text)
    
    def _setup_ui(self, text: str):
        """Setup message UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Role label
        role_label = QLabel("You" if self.is_user else "Assistant")
        role_font = QFont()
        role_font.setBold(True)
        role_label.setFont(role_font)
        
        if self.is_user:
            role_label.setStyleSheet("color: #2980b9;")
        else:
            role_label.setStyleSheet("color: #27ae60;")
        
        layout.addWidget(role_label)
        
        # Message text
        message_label = QLabel(text)
        message_label.setWordWrap(True)
        message_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(message_label)
        
        # Styling
        if self.is_user:
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #e3f2fd;
                    border-radius: 8px;
                    margin: 5px 20px 5px 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                ChatMessage {
                    background-color: #f1f8e9;
                    border-radius: 8px;
                    margin: 5px 5px 5px 20px;
                }
            """)


class ChatWorker(QThread):
    """Worker thread for chat processing."""
    
    response_ready = Signal(str)
    error_occurred = Signal(str)
    chunk_received = Signal(str)  # For streaming
    
    def __init__(self, llm, search_engine, question: str, max_chunks: int = 5):
        super().__init__()
        self.llm = llm
        self.search_engine = search_engine
        self.question = question
        self.max_chunks = max_chunks
    
    def run(self):
        """Process question and generate response."""
        try:
            # Search for relevant documents
            logger.debug(f"Searching for context: {self.question}")
            search_results = self.search_engine.search(
                query=self.question,
                top_k=self.max_chunks,
                semantic_only=True
            )
            
            # Prepare context chunks
            context_chunks = []
            for result in search_results:
                if hasattr(result, 'to_dict'):
                    result_dict = result.to_dict()
                else:
                    result_dict = result
                
                context_chunks.append({
                    'text': result_dict.get('text', ''),
                    'metadata': result_dict.get('metadata', {})
                })
            
            # Generate answer
            logger.debug("Generating answer with LLM")
            
            if self.llm.supports_streaming:
                # Streaming response
                full_response = ""
                for chunk in self.llm.generate_stream(
                    self.llm._build_rag_prompt(self.question, context_chunks)
                ):
                    full_response += chunk
                    self.chunk_received.emit(chunk)
                
                self.response_ready.emit(full_response)
            else:
                # Non-streaming response
                response = self.llm.answer_question(
                    question=self.question,
                    context_chunks=context_chunks,
                    stream=False
                )
                
                if response.success:
                    self.response_ready.emit(response.text)
                else:
                    self.error_occurred.emit(response.error or "Unknown error")
                    
        except Exception as e:
            logger.error(f"Error in chat worker: {e}")
            self.error_occurred.emit(str(e))


class ChatTab(QWidget):
    """
    Chat tab for AI-powered Q&A.
    
    Features:
    - Conversational interface
    - RAG-based answers from documents
    - Streaming responses (if supported)
    """
    
    # Signals
    question_asked = Signal(str)
    error_occurred = Signal(str)
    
    def __init__(self, config: dict, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        self.config = config
        self.llm = None
        self.search_engine = None
        self.chat_history = []
        self.current_worker = None
        
        self._setup_ui()
        self._setup_connections()
        
        logger.info("Chat tab initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Info message
        info_box = QGroupBox("AI Chat")
        info_layout = QVBoxLayout(info_box)
        
        info_label = QLabel(
            "Ask questions about your documents. The AI will search for relevant "
            "information and provide answers based on the retrieved context."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet("color: #555; padding: 10px;")
        info_layout.addWidget(info_label)
        
        layout.addWidget(info_box)
        
        # Chat display area
        self.chat_scroll = QScrollArea()
        self.chat_scroll.setWidgetResizable(True)
        self.chat_scroll.setStyleSheet("border: 1px solid #ddd; background: white;")
        
        self.chat_container = QWidget()
        self.chat_layout = QVBoxLayout(self.chat_container)
        self.chat_layout.setAlignment(Qt.AlignTop)
        self.chat_layout.setSpacing(10)
        
        self.chat_scroll.setWidget(self.chat_container)
        layout.addWidget(self.chat_scroll)
        
        # Input area
        input_group = QGroupBox("Your Question")
        input_layout = QVBoxLayout(input_group)
        
        input_row = QHBoxLayout()
        
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question about your documents...")
        self.question_input.setMinimumHeight(45)
        input_row.addWidget(self.question_input, stretch=4)
        
        self.ask_btn = QPushButton("💬 Ask")
        self.ask_btn.setMinimumHeight(45)
        self.ask_btn.setMinimumWidth(100)
        input_row.addWidget(self.ask_btn)
        
        self.clear_btn = QPushButton("🗑️ Clear")
        self.clear_btn.setMinimumHeight(45)
        input_row.addWidget(self.clear_btn)
        
        input_layout.addLayout(input_row)
        
        # Status label
        self.status_label = QLabel("Ready to answer questions")
        self.status_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        input_layout.addWidget(self.status_label)
        
        layout.addWidget(input_group)
        
        # Add initial greeting
        self._add_assistant_message(
            "Hello! I'm ready to answer questions about your documents. "
            "What would you like to know?"
        )
    
    def _setup_connections(self):
        """Setup signal/slot connections."""
        self.ask_btn.clicked.connect(self._ask_question)
        self.question_input.returnPressed.connect(self._ask_question)
        self.clear_btn.clicked.connect(self._clear_chat)
    
    def set_llm(self, llm):
        """Set the LLM instance."""
        self.llm = llm
        logger.info("LLM connected to chat tab")
    
    def set_search_engine(self, engine):
        """Set the search engine instance."""
        self.search_engine = engine
        logger.info("Search engine connected to chat tab")
    
    def _ask_question(self):
        """Process user question."""
        question = self.question_input.text().strip()
        
        if not question:
            return
        
        if self.llm is None:
            self.error_occurred.emit("LLM not initialized. Check settings.")
            return
        
        if self.search_engine is None:
            self.error_occurred.emit("Search engine not initialized.")
            return
        
        logger.info(f"User question: {question}")
        
        # Add user message
        self._add_user_message(question)
        
        # Clear input
        self.question_input.clear()
        
        # Disable input while processing
        self._set_input_enabled(False)
        self.status_label.setText("Thinking...")
        
        # Emit signal
        self.question_asked.emit(question)
        
        # Start worker thread
        self.current_worker = ChatWorker(
            self.llm,
            self.search_engine,
            question,
            max_chunks=5
        )
        
        self.current_worker.response_ready.connect(self._on_response_ready)
        self.current_worker.error_occurred.connect(self._on_error)
        self.current_worker.chunk_received.connect(self._on_chunk_received)
        self.current_worker.finished.connect(lambda: self._set_input_enabled(True))
        
        self.current_worker.start()
    
    def _on_response_ready(self, response: str):
        """Handle complete response."""
        if not hasattr(self, '_streaming_message'):
            # Non-streaming mode
            self._add_assistant_message(response)
        
        self.status_label.setText("Ready to answer questions")
        logger.info("Response complete")
    
    def _on_chunk_received(self, chunk: str):
        """Handle streaming chunk."""
        if not hasattr(self, '_streaming_message'):
            # Create streaming message widget
            self._streaming_message = ChatMessage("", False)
            self.chat_layout.addWidget(self._streaming_message)
            self._scroll_to_bottom()
            self._streaming_text = ""
        
        # Append chunk
        self._streaming_text += chunk
        
        # Update message
        message_label = self._streaming_message.findChild(QLabel)
        if message_label:
            message_label.setText(self._streaming_text)
        
        self._scroll_to_bottom()
    
    def _on_error(self, error_msg: str):
        """Handle error."""
        self._add_assistant_message(f"Error: {error_msg}")
        self.status_label.setText("Error occurred")
        self.error_occurred.emit(error_msg)
        self._set_input_enabled(True)
        
        # Clean up streaming message
        if hasattr(self, '_streaming_message'):
            delattr(self, '_streaming_message')
            delattr(self, '_streaming_text')
    
    def _add_user_message(self, text: str):
        """Add user message to chat."""
        message = ChatMessage(text, is_user=True)
        self.chat_layout.addWidget(message)
        self.chat_history.append(('user', text))
        self._scroll_to_bottom()
    
    def _add_assistant_message(self, text: str):
        """Add assistant message to chat."""
        # Clean up streaming message if exists
        if hasattr(self, '_streaming_message'):
            delattr(self, '_streaming_message')
            delattr(self, '_streaming_text')
        
        message = ChatMessage(text, is_user=False)
        self.chat_layout.addWidget(message)
        self.chat_history.append(('assistant', text))
        self._scroll_to_bottom()
    
    def _scroll_to_bottom(self):
        """Scroll chat to bottom."""
        scrollbar = self.chat_scroll.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def _set_input_enabled(self, enabled: bool):
        """Enable/disable input controls."""
        self.question_input.setEnabled(enabled)
        self.ask_btn.setEnabled(enabled)
    
    def _clear_chat(self):
        """Clear chat history."""
        # Remove all messages except the greeting
        while self.chat_layout.count() > 1:
            item = self.chat_layout.takeAt(1)
            if item.widget():
                item.widget().deleteLater()
        
        self.chat_history = []
        self.status_label.setText("Chat cleared. Ready for new questions.")
        
        logger.info("Chat cleared")
    
    def update_config(self, config: dict):
        """Update configuration."""
        self.config = config
        logger.info("Chat tab config updated")
    
    def is_ready(self) -> bool:
        """Check if chat is ready."""
        return self.llm is not None and self.search_engine is not None