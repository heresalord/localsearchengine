"""
File system watcher for automatic re-indexing.
"""

import logging
import time
from pathlib import Path
from typing import Callable, Optional, Set
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEventHandler,
    FileCreatedEvent,
    FileModifiedEvent,
    FileDeletedEvent,
    FileMovedEvent
)

logger = logging.getLogger(__name__)


class DocumentFileHandler(FileSystemEventHandler):
    """
    File system event handler for document changes.
    
    Monitors supported file types and triggers callbacks for:
    - File creation
    - File modification
    - File deletion
    - File moves
    """
    
    def __init__(
        self,
        supported_extensions: Set[str],
        on_created: Optional[Callable[[str], None]] = None,
        on_modified: Optional[Callable[[str], None]] = None,
        on_deleted: Optional[Callable[[str], None]] = None,
        debounce_seconds: float = 2.0
    ):
        """
        Initialize file handler.
        
        Args:
            supported_extensions: Set of file extensions to monitor (e.g., {'.pdf', '.txt'})
            on_created: Callback for file creation (file_path)
            on_modified: Callback for file modification (file_path)
            on_deleted: Callback for file deletion (file_path)
            debounce_seconds: Time to wait before triggering callback (prevents duplicate events)
        """
        super().__init__()
        
        self.supported_extensions = {ext.lower() for ext in supported_extensions}
        self.on_created_callback = on_created
        self.on_modified_callback = on_modified
        self.on_deleted_callback = on_deleted
        self.debounce_seconds = debounce_seconds
        
        # Debouncing: track recent events to avoid duplicates
        self.recent_events = {}  # {file_path: (event_type, timestamp)}
        
        logger.info(f"File handler initialized for extensions: {supported_extensions}")
    
    def _is_supported(self, path: str) -> bool:
        """Check if file extension is supported."""
        return Path(path).suffix.lower() in self.supported_extensions
    
    def _should_process(self, path: str, event_type: str) -> bool:
        """
        Check if event should be processed (debouncing).
        
        Args:
            path: File path
            event_type: Event type ('created', 'modified', 'deleted')
            
        Returns:
            True if event should be processed
        """
        now = time.time()
        
        if path in self.recent_events:
            last_type, last_time = self.recent_events[path]
            
            # If same event type within debounce period, skip
            if last_type == event_type and (now - last_time) < self.debounce_seconds:
                logger.debug(f"Debouncing {event_type} event for {path}")
                return False
        
        # Update recent events
        self.recent_events[path] = (event_type, now)
        
        # Clean up old entries (older than debounce period)
        cutoff = now - self.debounce_seconds * 2
        self.recent_events = {
            p: (t, ts) for p, (t, ts) in self.recent_events.items()
            if ts > cutoff
        }
        
        return True
    
    def on_created(self, event: FileCreatedEvent):
        """Handle file creation."""
        if event.is_directory:
            return
        
        path = event.src_path
        
        if not self._is_supported(path):
            return
        
        if not self._should_process(path, 'created'):
            return
        
        logger.info(f"File created: {path}")
        
        if self.on_created_callback:
            try:
                self.on_created_callback(path)
            except Exception as e:
                logger.error(f"Error in on_created callback: {e}")
    
    def on_modified(self, event: FileModifiedEvent):
        """Handle file modification."""
        if event.is_directory:
            return
        
        path = event.src_path
        
        if not self._is_supported(path):
            return
        
        if not self._should_process(path, 'modified'):
            return
        
        logger.info(f"File modified: {path}")
        
        if self.on_modified_callback:
            try:
                self.on_modified_callback(path)
            except Exception as e:
                logger.error(f"Error in on_modified callback: {e}")
    
    def on_deleted(self, event: FileDeletedEvent):
        """Handle file deletion."""
        if event.is_directory:
            return
        
        path = event.src_path
        
        if not self._is_supported(path):
            return
        
        if not self._should_process(path, 'deleted'):
            return
        
        logger.info(f"File deleted: {path}")
        
        if self.on_deleted_callback:
            try:
                self.on_deleted_callback(path)
            except Exception as e:
                logger.error(f"Error in on_deleted callback: {e}")
    
    def on_moved(self, event: FileMovedEvent):
        """Handle file move/rename."""
        if event.is_directory:
            return
        
        src_path = event.src_path
        dest_path = event.dest_path
        
        # Treat as delete + create
        if self._is_supported(src_path):
            logger.info(f"File moved from: {src_path}")
            if self.on_deleted_callback:
                try:
                    self.on_deleted_callback(src_path)
                except Exception as e:
                    logger.error(f"Error in on_deleted callback: {e}")
        
        if self._is_supported(dest_path):
            logger.info(f"File moved to: {dest_path}")
            if self.on_created_callback:
                try:
                    self.on_created_callback(dest_path)
                except Exception as e:
                    logger.error(f"Error in on_created callback: {e}")


class FileWatcher:
    """
    File system watcher for automatic document monitoring.
    
    Features:
    - Monitors directory for file changes
    - Triggers callbacks for create/modify/delete events
    - Debouncing to prevent duplicate events
    - Graceful start/stop
    """
    
    def __init__(
        self,
        directory: str,
        supported_extensions: Set[str],
        on_created: Optional[Callable[[str], None]] = None,
        on_modified: Optional[Callable[[str], None]] = None,
        on_deleted: Optional[Callable[[str], None]] = None,
        recursive: bool = True,
        debounce_seconds: float = 2.0
    ):
        """
        Initialize file watcher.
        
        Args:
            directory: Directory to watch
            supported_extensions: File extensions to monitor
            on_created: Callback for file creation
            on_modified: Callback for file modification
            on_deleted: Callback for file deletion
            recursive: Whether to watch subdirectories
            debounce_seconds: Debounce time for events
        """
        self.directory = Path(directory)
        self.recursive = recursive
        
        if not self.directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        if not self.directory.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")
        
        # Create event handler
        self.event_handler = DocumentFileHandler(
            supported_extensions=supported_extensions,
            on_created=on_created,
            on_modified=on_modified,
            on_deleted=on_deleted,
            debounce_seconds=debounce_seconds
        )
        
        # Create observer
        self.observer = Observer()
        self.is_running = False
        
        logger.info(
            f"FileWatcher initialized for {directory} "
            f"(recursive: {recursive})"
        )
    
    def start(self):
        """Start watching the directory."""
        if self.is_running:
            logger.warning("FileWatcher already running")
            return
        
        logger.info(f"Starting FileWatcher on {self.directory}")
        
        self.observer.schedule(
            self.event_handler,
            str(self.directory),
            recursive=self.recursive
        )
        
        self.observer.start()
        self.is_running = True
        
        logger.info("FileWatcher started successfully")
    
    def stop(self):
        """Stop watching the directory."""
        if not self.is_running:
            logger.warning("FileWatcher not running")
            return
        
        logger.info("Stopping FileWatcher")
        
        self.observer.stop()
        self.observer.join(timeout=5)
        self.is_running = False
        
        logger.info("FileWatcher stopped")
    
    def restart(self):
        """Restart the watcher."""
        logger.info("Restarting FileWatcher")
        self.stop()
        time.sleep(0.5)  # Brief pause
        self.observer = Observer()  # Create new observer
        self.start()
    
    def update_directory(self, new_directory: str):
        """
        Update watched directory.
        
        Args:
            new_directory: New directory path
        """
        new_path = Path(new_directory)
        
        if not new_path.exists() or not new_path.is_dir():
            raise ValueError(f"Invalid directory: {new_directory}")
        
        was_running = self.is_running
        
        if was_running:
            self.stop()
        
        self.directory = new_path
        logger.info(f"Updated watch directory to: {new_directory}")
        
        # Create a new observer (can't restart old one)
        if was_running:
            self.observer = Observer()
            self.start()
    
    def update_callbacks(
        self,
        on_created: Optional[Callable[[str], None]] = None,
        on_modified: Optional[Callable[[str], None]] = None,
        on_deleted: Optional[Callable[[str], None]] = None
    ):
        """
        Update event callbacks.
        
        Args:
            on_created: New callback for file creation
            on_modified: New callback for file modification
            on_deleted: New callback for file deletion
        """
        if on_created is not None:
            self.event_handler.on_created_callback = on_created
        
        if on_modified is not None:
            self.event_handler.on_modified_callback = on_modified
        
        if on_deleted is not None:
            self.event_handler.on_deleted_callback = on_deleted
        
        logger.info("FileWatcher callbacks updated")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()


# Example usage
if __name__ == "__main__":
    import sys
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Callbacks
    def on_file_created(path: str):
        print(f"✅ Created: {path}")
    
    def on_file_modified(path: str):
        print(f"📝 Modified: {path}")
    
    def on_file_deleted(path: str):
        print(f"❌ Deleted: {path}")
    
    # Watch current directory
    watch_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    
    print(f"\n👀 Watching: {watch_dir}")
    print("Press Ctrl+C to stop\n")
    
    try:
        with FileWatcher(
            directory=watch_dir,
            supported_extensions={'.txt', '.md', '.pdf', '.docx'},
            on_created=on_file_created,
            on_modified=on_file_modified,
            on_deleted=on_file_deleted,
            recursive=True
        ) as watcher:
            # Keep running
            while True:
                time.sleep(1)
    
    except KeyboardInterrupt:
        print("\n\n👋 Stopping watcher...")
    except Exception as e:
        print(f"\n❌ Error: {e}")