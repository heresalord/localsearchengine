"""
Document indexing orchestration.
"""

import logging
from typing import List, Optional, Callable, Dict, Any
from pathlib import Path
import hashlib
import time

from .file_loader import FileLoader
from .chunker import TextChunker
from .embeddings import EmbeddingGenerator
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class DocumentIndexer:
    """
    Orchestrates the indexing pipeline:
    Load → Chunk → Embed → Store
    
    Features:
    - Batch processing for efficiency
    - Progress tracking with callbacks
    - Incremental indexing (skip unchanged files)
    - Error handling and logging
    """
    
    def __init__(
        self,
        file_loader: FileLoader,
        chunker: TextChunker,
        embedder: EmbeddingGenerator,
        vector_store: VectorStore,
        batch_size: int = 50
    ):
        """
        Initialize the indexer.
        
        Args:
            file_loader: File loading component
            chunker: Text chunking component
            embedder: Embedding generation component
            vector_store: Vector storage component
            batch_size: Number of chunks to process at once
        """
        self.file_loader = file_loader
        self.chunker = chunker
        self.embedder = embedder
        self.vector_store = vector_store
        self.batch_size = batch_size
        
        logger.info("DocumentIndexer initialized")
    
    def index_directory(
        self,
        directory: str,
        recursive: bool = True,
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> Dict[str, Any]:
        """
        Index all supported files in a directory.
        
        Args:
            directory: Directory path to index
            recursive: Whether to index subdirectories
            progress_callback: Callback function(current, total, filename)
            
        Returns:
            Dictionary with indexing statistics
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        
        logger.info(f"Starting indexing of directory: {directory} (recursive: {recursive})")
        start_time = time.time()
        
        # Find all supported files
        files = self._find_files(dir_path, recursive)
        total_files = len(files)
        
        logger.info(f"Found {total_files} supported files")
        
        if total_files == 0:
            return {
                'total_files': 0,
                'indexed_files': 0,
                'skipped_files': 0,
                'failed_files': 0,
                'total_chunks': 0,
                'duration': 0
            }
        
        # Get existing file hashes to detect changes
        existing_hashes = self._get_existing_file_hashes()
        
        stats = {
            'total_files': total_files,
            'indexed_files': 0,
            'skipped_files': 0,
            'failed_files': 0,
            'total_chunks': 0
        }
        
        # Process files
        for i, file_path in enumerate(files):
            if progress_callback:
                progress_callback(i + 1, total_files, file_path.name)
            
            try:
                # Check if file needs reindexing
                file_hash = self._compute_file_hash(file_path)
                
                if str(file_path) in existing_hashes and existing_hashes[str(file_path)] == file_hash:
                    logger.debug(f"Skipping unchanged file: {file_path.name}")
                    stats['skipped_files'] += 1
                    continue
                
                # Remove old chunks if file was previously indexed
                if str(file_path) in existing_hashes:
                    self._remove_file_chunks(str(file_path))
                
                # Index the file
                chunks_created = self.index_file(str(file_path), file_hash)
                
                if chunks_created > 0:
                    stats['indexed_files'] += 1
                    stats['total_chunks'] += chunks_created
                else:
                    stats['failed_files'] += 1
                    
            except Exception as e:
                logger.error(f"Error indexing {file_path.name}: {e}")
                stats['failed_files'] += 1
        
        duration = time.time() - start_time
        stats['duration'] = duration
        
        logger.info(
            f"Indexing complete: {stats['indexed_files']} indexed, "
            f"{stats['skipped_files']} skipped, {stats['failed_files']} failed "
            f"in {duration:.2f}s"
        )
        
        return stats
    
    def index_file(self, file_path: str, file_hash: Optional[str] = None) -> int:
        """
        Index a single file.
        
        Args:
            file_path: Path to the file
            file_hash: Precomputed file hash (optional)
            
        Returns:
            Number of chunks created
        """
        logger.debug(f"Indexing file: {file_path}")
        
        # Load file
        loaded = self.file_loader.load(file_path)
        if not loaded:
            logger.warning(f"Failed to load file: {file_path}")
            return 0
        
        text = loaded['text']
        metadata = loaded['metadata']
        
        # Add file hash to metadata
        if file_hash is None:
            file_hash = self._compute_file_hash(Path(file_path))
        metadata['file_hash'] = file_hash
        
        # Chunk text
        chunks = self.chunker.chunk(text, metadata)
        if not chunks:
            logger.warning(f"No chunks created for: {file_path}")
            return 0
        
        # Process in batches
        total_chunks = len(chunks)
        for batch_start in range(0, total_chunks, self.batch_size):
            batch_end = min(batch_start + self.batch_size, total_chunks)
            batch = chunks[batch_start:batch_end]
            
            self._process_batch(batch)
        
        logger.info(f"Indexed {total_chunks} chunks from {Path(file_path).name}")
        return total_chunks
    
    def _process_batch(self, batch: List[Dict[str, Any]]) -> None:
        """
        Process a batch of chunks: embed and store.
        
        Args:
            batch: List of chunk dictionaries
        """
        # Extract texts
        texts = [chunk['text'] for chunk in batch]
        
        # Generate embeddings
        embeddings = self.embedder.generate(texts, batch_size=len(texts))
        
        # Generate IDs (hash of file_path + chunk_index)
        ids = []
        metadatas = []
        
        for chunk in batch:
            meta = chunk['metadata']
            chunk_id = self._generate_chunk_id(
                meta['file_path'],
                meta['chunk_index']
            )
            ids.append(chunk_id)
            metadatas.append(meta)
        
        # Store in vector database
        self.vector_store.add_documents(
            ids=ids,
            texts=texts,
            embeddings=embeddings,
            metadatas=metadatas
        )
    
    def _find_files(self, directory: Path, recursive: bool) -> List[Path]:
        """Find all supported files in directory."""
        files = []
        
        pattern = "**/*" if recursive else "*"
        
        for path in directory.glob(pattern):
            if path.is_file() and FileLoader.is_supported(str(path)):
                files.append(path)
        
        return sorted(files)
    
    def _compute_file_hash(self, file_path: Path) -> str:
        """Compute MD5 hash of file for change detection."""
        hasher = hashlib.md5()
        
        # Hash file metadata (size + mtime) for speed
        # For more accuracy, could hash actual content
        stat = file_path.stat()
        hash_input = f"{stat.st_size}:{stat.st_mtime}".encode()
        hasher.update(hash_input)
        
        return hasher.hexdigest()
    
    def _get_existing_file_hashes(self) -> Dict[str, str]:
        """Get file hashes of all indexed files."""
        hashes = {}
        
        try:
            all_docs = self.vector_store.collection.get(include=["metadatas"])
            
            for meta in all_docs['metadatas']:
                file_path = meta.get('file_path')
                file_hash = meta.get('file_hash')
                
                if file_path and file_hash:
                    hashes[file_path] = file_hash
                    
        except Exception as e:
            logger.error(f"Error getting existing file hashes: {e}")
        
        return hashes
    
    def _remove_file_chunks(self, file_path: str) -> None:
        """Remove all chunks associated with a file."""
        try:
            results = self.vector_store.get_by_filter({'file_path': file_path})
            
            if results['ids']:
                self.vector_store.delete_documents(results['ids'])
                logger.debug(f"Removed {len(results['ids'])} old chunks for {file_path}")
                
        except Exception as e:
            logger.error(f"Error removing old chunks: {e}")
    
    @staticmethod
    def _generate_chunk_id(file_path: str, chunk_index: int) -> str:
        """Generate unique ID for a chunk."""
        # Use hash of file path + chunk index
        unique_str = f"{file_path}::{chunk_index}"
        return hashlib.md5(unique_str.encode()).hexdigest()