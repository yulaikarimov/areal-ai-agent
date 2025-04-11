"""
Document processing module for loading, chunking, and metadata extraction.

This module provides functionality to load documents from various formats,
split them into manageable chunks, and attach proper metadata including
RBAC information (allowed_roles) for secure retrieval.
"""

# Import necessary libraries
from pathlib import Path
from typing import List, Dict, Any, Optional, Generator, Tuple
import logging
import re

# LangChain imports
from langchain_core.documents import Document
from langchain_community.document_loaders import UnstructuredFileLoader, UnstructuredMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

logger = logging.getLogger(__name__)

class DocumentProcessor:
    """
    Handles the loading, processing, and chunking of documents with metadata extraction.
    
    This class provides methods to load documents from various formats (PDF, DOCX, TXT, etc.),
    split them into appropriate chunks, and attach metadata including RBAC information
    for secure document retrieval.
    """
    
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        """
        Initialize the DocumentProcessor with specified chunking parameters.
        
        Args:
            chunk_size (int): The maximum size of each document chunk. Defaults to 1000.
            chunk_overlap (int): The overlap between consecutive chunks. Defaults to 200.
        """
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )
        logger.info(f"Initialized DocumentProcessor with chunk_size={chunk_size}, chunk_overlap={chunk_overlap}")
    
    def _extract_roles_from_path(self, file_path: Path) -> List[str]:
        """
        Extract role information from file path using naming conventions.
        
        Strategy B: Analyze the file path and parent directories to infer roles.
        
        Args:
            file_path (Path): The path to the document
            
        Returns:
            List[str]: A list of inferred roles based on the path
        """
        roles = []
        
        # Convert path parts to lowercase for case-insensitive matching
        path_str = str(file_path).lower()
        parent_dir = file_path.parent.name.lower()
        
        # Common role keywords to check for in paths
        role_keywords = {
            'public': ['public', 'external', 'customer'],
            'employee': ['employee', 'internal', 'staff', 'team'],
            'manager': ['manager', 'management', 'supervisor'],
            'hr': ['hr', 'human_resources', 'human-resources'],
            'finance': ['finance', 'financial', 'accounting'],
            'sales': ['sales', 'marketing'],
            'support': ['support', 'helpdesk', 'customer_service'],
            'tech': ['tech', 'technical', 'engineering', 'developer'],
            'legal': ['legal', 'compliance', 'regulatory']
        }
        
        # Check for role keywords in the path
        for role, keywords in role_keywords.items():
            for keyword in keywords:
                if keyword in path_str or keyword in parent_dir:
                    roles.append(role)
                    break  # Once we've added a role, no need to check other keywords
        
        # If we identified any roles, log them
        if roles:
            logger.debug(f"Inferred roles {roles} from path: {file_path}")
        else:
            logger.debug(f"No roles inferred from path: {file_path}")
            
        return roles
    
    def load_and_split_documents(
        self, 
        file_path: Path, 
        default_roles: Optional[List[str]] = None
    ) -> Generator[Document, None, None]:
        """
        Load a document, split it into chunks, and yield each chunk with proper metadata.
        
        This method loads a document from the specified file path, processes it to extract
        metadata including RBAC information, splits it into manageable chunks, and yields
        each chunk as a Document object.
        
        Args:
            file_path (Path): The path to the document to process
            default_roles (Optional[List[str]]): Default roles to assign if none are inferred
                
        Yields:
            Document: Processed document chunks with metadata
            
        Raises:
            FileNotFoundError: If the specified file does not exist
            ValueError: If there are issues processing the document
        """
        if not file_path.exists():
            error_msg = f"Document not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Ensure default_roles is a list, not None
        if default_roles is None:
            default_roles = []
            
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Load the document using appropriate loader based on extension
            file_suffix = file_path.suffix.lower()
            if file_suffix == '.md':
                logger.debug(f"Using UnstructuredMarkdownLoader for {file_path.name}")
                loader = UnstructuredMarkdownLoader(str(file_path), mode="elements")
            else:
                # Fallback to generic loader for other types (PDF, DOCX, etc.)
                logger.debug(f"Using UnstructuredFileLoader for {file_path.name}")
                loader = UnstructuredFileLoader(str(file_path), mode="elements")
                
            docs = loader.load()
            logger.info(f"Loaded {len(docs)} elements from {file_path}")
            
            # Process each element/document from the loader
            for doc_idx, doc in enumerate(docs):
                # Extract metadata and add source
                metadata = doc.metadata.copy()  # Start with existing metadata
                metadata['source'] = str(file_path.name)
                metadata['full_path'] = str(file_path)
                
                # Determine allowed roles (Strategy A + B)
                path_roles = self._extract_roles_from_path(file_path)
                roles = path_roles if path_roles else default_roles.copy()
                
                # Add the allowed_roles metadata - CRUCIAL for RBAC
                metadata['allowed_roles'] = roles
                logger.debug(f"Document chunk {doc_idx} from {file_path.name} assigned roles: {roles}")
                
                # Split the content into chunks
                text_chunks = self.text_splitter.split_text(doc.page_content)
                
                # If we got multiple chunks, create new Documents
                if len(text_chunks) > 1:
                    logger.debug(f"Split element {doc_idx} into {len(text_chunks)} chunks")
                    
                    # Create and yield a Document for each chunk, with copied metadata
                    for i, chunk in enumerate(text_chunks):
                        if not chunk.strip():  # Skip empty chunks
                            continue
                            
                        # Create a new metadata dict for each chunk to avoid cross-references
                        chunk_metadata = metadata.copy()
                        # Add chunk-specific metadata
                        chunk_metadata['chunk_id'] = f"{doc_idx}-{i}"
                        
                        # --- BEGIN ADDED LOGGING ---
                        logger.debug(f"Yielding chunk {chunk_metadata.get('chunk_id')} with metadata: {chunk_metadata}")
                        # --- END ADDED LOGGING ---
                        
                        yield Document(
                            page_content=chunk,
                            metadata=chunk_metadata
                        )
                # If there's only one chunk, use the original document with updated metadata
                elif text_chunks and text_chunks[0].strip():
                    # Update the metadata with chunk_id
                    metadata['chunk_id'] = f"{doc_idx}-0"
                    
                    # --- BEGIN ADDED LOGGING ---
                    logger.debug(f"Yielding single chunk {metadata.get('chunk_id')} with metadata: {metadata}")
                    # --- END ADDED LOGGING ---
                    
                    yield Document(
                        page_content=text_chunks[0],
                        metadata=metadata
                    )
        
        except Exception as e:
            error_msg = f"Error processing document {file_path}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ValueError(error_msg) from e 