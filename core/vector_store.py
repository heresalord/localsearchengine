"""
Vector storage and retrieval using ChromaDB.
"""

import logging
from typing import List, Dict, Optional, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings
import numpy as np

logger = logging.getLogger(__name__)


class VectorStore:
    """
    Wrapper for ChromaDB vector database.
    
    Handles:
    - Document storage with metadata
    - Similarity search
    - Incremental updates
    - Persistence
    """
    
    def __init__(self, persist_directory: str = "./chroma_db", collection_name: str = "documents"):
        """
        Initialize the vector store.
        
        Args:
            persist_directory: Path to store the database
            collection_name: Name of the collection
        """
        self.persist_directory = Path(persist_directory)
        self.collection_name = collection_name
        
        # Create directory if it doesn't exist
        self.persist_directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initializing VectorStore at {persist_directory}")
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=str(self.persist_directory),
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}  # Use cosine similarity
        )
        
        logger.info(f"Collection '{collection_name}' ready with {self.collection.count()} documents")
    
    def add_documents(
        self,
        ids: List[str],
        texts: List[str],
        embeddings: np.ndarray,
        metadatas: List[Dict[str, Any]]
    ) -> None:
        """
        Add documents to the vector store.
        
        Args:
            ids: Unique identifiers for each document
            texts: Document text content
            embeddings: Document embeddings
            metadatas: Metadata for each document (file_path, file_type, timestamp, etc.)
        """
        if not ids or len(ids) != len(texts) != len(embeddings) != len(metadatas):
            raise ValueError("All inputs must have the same length")
        
        logger.debug(f"Adding {len(ids)} documents to vector store")
        
        try:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings.tolist(),
                metadatas=metadatas
            )
            logger.info(f"Successfully added {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error adding documents: {e}")
            raise
    
    def search(
        self,
        query_embedding: np.ndarray,
        n_results: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, List]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query embedding vector
            n_results: Number of results to return
            filters: Metadata filters (e.g., {"file_type": "pdf"})
            
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas', 'distances'
        """
        logger.debug(f"Searching for {n_results} similar documents")
        
        try:
            results = self.collection.query(
                query_embeddings=[query_embedding.tolist()],
                n_results=n_results,
                where=filters,
                include=["documents", "metadatas", "distances"]
            )
            
            # Flatten results (query returns nested lists)
            flattened = {
                'ids': results['ids'][0] if results['ids'] else [],
                'documents': results['documents'][0] if results['documents'] else [],
                'metadatas': results['metadatas'][0] if results['metadatas'] else [],
                'distances': results['distances'][0] if results['distances'] else []
            }
            
            logger.debug(f"Found {len(flattened['ids'])} results")
            return flattened
            
        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            raise
    
    def update_document(
        self,
        doc_id: str,
        text: Optional[str] = None,
        embedding: Optional[np.ndarray] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update an existing document.
        
        Args:
            doc_id: Document ID to update
            text: New document text
            embedding: New embedding
            metadata: New metadata
        """
        logger.debug(f"Updating document: {doc_id}")
        
        try:
            update_data = {"ids": [doc_id]}
            
            if text is not None:
                update_data["documents"] = [text]
            if embedding is not None:
                update_data["embeddings"] = [embedding.tolist()]
            if metadata is not None:
                update_data["metadatas"] = [metadata]
            
            self.collection.update(**update_data)
            logger.info(f"Updated document: {doc_id}")
            
        except Exception as e:
            logger.error(f"Error updating document {doc_id}: {e}")
            raise
    
    def delete_documents(self, ids: List[str]) -> None:
        """
        Delete documents by IDs.
        
        Args:
            ids: List of document IDs to delete
        """
        logger.debug(f"Deleting {len(ids)} documents")
        
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Error deleting documents: {e}")
            raise
    
    def get_by_filter(self, filters: Dict[str, Any], limit: Optional[int] = None) -> Dict[str, List]:
        """
        Get documents matching metadata filters.
        
        Args:
            filters: Metadata filters
            limit: Maximum number of results
            
        Returns:
            Dictionary with 'ids', 'documents', 'metadatas'
        """
        logger.debug(f"Filtering documents with: {filters}")
        
        try:
            results = self.collection.get(
                where=filters,
                limit=limit,
                include=["documents", "metadatas"]
            )
            
            logger.debug(f"Found {len(results['ids'])} matching documents")
            return results
            
        except Exception as e:
            logger.error(f"Error filtering documents: {e}")
            raise
    
    def count(self) -> int:
        """Get total number of documents in the collection."""
        return self.collection.count()
    
    def reset(self) -> None:
        """Delete all documents in the collection."""
        logger.warning("Resetting vector store - all documents will be deleted")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Vector store reset complete")
    
    def get_all_file_paths(self) -> List[str]:
        """
        Get all unique file paths in the database.
        
        Returns:
            List of file paths
        """
        try:
            all_docs = self.collection.get(include=["metadatas"])
            file_paths = list(set(
                meta.get('file_path', '') 
                for meta in all_docs['metadatas']
            ))
            return [fp for fp in file_paths if fp]
        except Exception as e:
            logger.error(f"Error getting file paths: {e}")
            return []