"""
Logging configuration for the application.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logger(
    name: str = "search_engine",
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_dir: str = "./logs",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    console_output: bool = True
) -> logging.Logger:
    """
    Setup application logger with file and console handlers.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Log file name (default: search_engine.log)
        log_dir: Directory for log files
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup files to keep
        console_output: Whether to output to console
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(simple_formatter)
        logger.addHandler(console_handler)
    
    # File handler (with rotation)
    if log_file is None:
        log_file = f"{name}.log"
    
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    
    file_path = log_path / log_file
    
    file_handler = RotatingFileHandler(
        filename=str(file_path),
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(detailed_formatter)
    logger.addHandler(file_handler)
    
    # Log initial message
    logger.info("=" * 80)
    logger.info(f"Logger '{name}' initialized")
    logger.info(f"Log level: {logging.getLevelName(level)}")
    logger.info(f"Log file: {file_path}")
    logger.info("=" * 80)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


def set_log_level(level: int):
    """
    Set logging level for all handlers.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    
    for handler in root_logger.handlers:
        if isinstance(handler, logging.StreamHandler):
            handler.setLevel(level)


class LoggerContext:
    """
    Context manager for temporarily changing log level.
    
    Usage:
        with LoggerContext(logging.DEBUG):
            # Code that needs debug logging
            pass
    """
    
    def __init__(self, level: int, logger: Optional[logging.Logger] = None):
        """
        Initialize context.
        
        Args:
            level: Temporary log level
            logger: Specific logger (default: root logger)
        """
        self.level = level
        self.logger = logger or logging.getLogger()
        self.original_level = None
    
    def __enter__(self):
        """Enter context."""
        self.original_level = self.logger.level
        self.logger.setLevel(self.level)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        self.logger.setLevel(self.original_level)


def log_exception(logger: logging.Logger, message: str = "Exception occurred"):
    """
    Decorator to log exceptions in functions.
    
    Args:
        logger: Logger instance
        message: Custom error message
        
    Usage:
        @log_exception(logger)
        def my_function():
            pass
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.exception(f"{message}: {e}")
                raise
        return wrapper
    return decorator


def configure_third_party_loggers(level: int = logging.WARNING):
    """
    Configure logging levels for third-party libraries.
    
    Prevents verbose output from dependencies.
    
    Args:
        level: Logging level for third-party libraries
    """
    third_party = [
        'urllib3',
        'requests',
        'chromadb',
        'sentence_transformers',
        'transformers',
        'torch',
        'PIL',
        'matplotlib',
    ]
    
    for lib in third_party:
        logging.getLogger(lib).setLevel(level)


# Example usage and testing
if __name__ == "__main__":
    # Setup logger
    logger = setup_logger(
        name="test_logger",
        level=logging.DEBUG,
        log_file="test.log"
    )
    
    # Test logging at different levels
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")
    logger.critical("This is a critical message")
    
    # Test exception logging
    try:
        raise ValueError("Test exception")
    except Exception:
        logger.exception("Caught an exception")
    
    # Test context manager
    logger.info("Current level: INFO")
    with LoggerContext(logging.DEBUG, logger):
        logger.debug("Temporarily in DEBUG mode")
    logger.debug("Back to INFO mode (this won't show)")
    logger.info("Back to INFO mode (this will show)")
    
    print("\nCheck ./logs/test.log for detailed output")