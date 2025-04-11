#!/usr/bin/env python
"""
Script for loading documents into the Qdrant vector database.

This script processes documents from a specified directory, extracts their content,
generates embeddings, and uploads them to Qdrant for later retrieval. It also handles
metadata extraction including RBAC information based on file paths or defaults.
"""

# Import necessary libraries
import argparse
import logging
import time
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import uuid

# Import project components
from src.config.settings import settings
from src.knowledge.document_processor import DocumentProcessor
from src.knowledge.qdrant_manager import qdrant_manager
from src.config.embedding_factory import get_embedding_model
from qdrant_client.http import models as rest
from langchain_core.documents import Document

# Configure basic logging (can be enhanced with src.utils.logging_config if it exists)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
logger = logging.getLogger("knowledge_base_loader")


def get_vector_size(model_name: str) -> int:
    """
    Determine the vector size for a given embedding model name.
    
    Args:
        model_name: The name of the embedding model.
        
    Returns:
        int: The vector size for the specified model.
    """
    # Known model sizes
    if "text-embedding-3-small" in model_name:
        return 1536
    elif "text-embedding-3-large" in model_name:
        return 3072
    elif "text-embedding-ada-002" in model_name:
        return 1536
    elif "e5-" in model_name.lower():  # HuggingFace E5 family
        return 1024
    # Add cases for other potential embedding models as needed
    else:
        logger.warning(f"Unknown embedding model '{model_name}' for vector size. Defaulting to 1536.")
        return 1536


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Load and index documents into the Qdrant vector database."
    )
    parser.add_argument(
        "--docs_dir", 
        type=str, 
        default="data/docs_to_ingest",
        help="Path to the directory containing documents to ingest."
    )
    parser.add_argument(
        "--default_roles", 
        type=str, 
        default="public",
        help="Comma-separated list of default roles (e.g., 'employee,public')."
    )
    parser.add_argument(
        "--recreate_collection", 
        action="store_true",
        help="Delete and recreate the Qdrant collection before ingestion."
    )
    parser.add_argument(
        "--batch_size", 
        type=int, 
        default=64,
        help="Number of documents to process in each batch for embedding and upload."
    )
    parser.add_argument(
        "--chunk_size", 
        type=int, 
        default=1000,
        help="Size of text chunks for document splitting."
    )
    parser.add_argument(
        "--chunk_overlap", 
        type=int, 
        default=200,
        help="Overlap between text chunks for document splitting."
    )
    
    return parser.parse_args()


def process_documents(
    docs_dir: Path,
    default_roles: List[str],
    processor: DocumentProcessor,
    embedding_model: Any,
    batch_size: int
) -> Tuple[int, int]:
    """
    Process documents from the specified directory, generate embeddings,
    and upload them to Qdrant.
    
    Args:
        docs_dir: Path to the directory containing documents
        default_roles: Default roles to assign if none are inferred
        processor: The DocumentProcessor instance
        embedding_model: The embedding model to use
        batch_size: Number of chunks to process in each batch
        
    Returns:
        Tuple[int, int]: Number of files and chunks processed
    """
    total_files = 0
    total_chunks = 0
    batch_chunks = []
    start_time = time.time()
    
    # Get all files recursively
    all_files = list(docs_dir.rglob('*'))
    logger.info(f"Found {len(all_files)} potential files to process")
    
    for file_idx, file_path in enumerate(all_files):
        # Skip directories
        if file_path.is_dir():
            continue
            
        try:
            logger.info(f"Processing file {file_idx+1}/{len(all_files)}: {file_path.relative_to(docs_dir)}")
            
            # Collect chunks from this document
            file_chunks = 0
            for chunk in processor.load_and_split_documents(file_path, default_roles=default_roles):
                batch_chunks.append(chunk)
                file_chunks += 1
                
                # Process batch if it's full
                if len(batch_chunks) >= batch_size:
                    process_batch(batch_chunks, embedding_model)
                    total_chunks += len(batch_chunks)
                    batch_chunks = []
                    
            logger.info(f"Extracted {file_chunks} chunks from {file_path.name}")
            total_files += 1
            
            # Show progress periodically
            if total_files % 10 == 0:
                elapsed_time = time.time() - start_time
                logger.info(
                    f"Progress: {total_files} files and {total_chunks + len(batch_chunks)} "
                    f"chunks processed in {elapsed_time:.1f}s"
                )
                
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}", exc_info=True)
            
    # Process any remaining chunks in the last batch
    if batch_chunks:
        process_batch(batch_chunks, embedding_model)
        total_chunks += len(batch_chunks)
        
    return total_files, total_chunks


def process_batch(batch_chunks: List[Document], embedding_model: Any) -> None:
    """
    Process a batch of document chunks: generate embeddings and upload to Qdrant.
    
    Args:
        batch_chunks: List of Document chunks to process
        embedding_model: The embedding model to use
    """
    if not batch_chunks:
        return
        
    # Extract texts for embedding
    batch_texts = [chunk.page_content for chunk in batch_chunks]
    
    try:
        # Generate embeddings
        logger.debug(f"Generating embeddings for {len(batch_texts)} chunks")
        batch_embeddings = embedding_model.embed_documents(batch_texts)
        
        # Prepare Qdrant points
        qdrant_points = []
        for i, (chunk, embedding) in enumerate(zip(batch_chunks, batch_embeddings)):
            # Generate a unique ID for Qdrant Point
            point_id = uuid.uuid4().hex # ALWAYS generate a UUID for the Qdrant ID
            
            # Prepare payload - keep original chunk_id here if needed
            payload = chunk.metadata.copy()
            payload['text'] = chunk.page_content  # Ensure text is in payload for retrieval
            
            # Create point
            qdrant_point = rest.PointStruct(
                id=point_id,
                vector=embedding,
                payload=payload
            )
            qdrant_points.append(qdrant_point)
            
        # Upload to Qdrant
        logger.debug(f"Upserting {len(qdrant_points)} points to Qdrant")
        result = qdrant_manager.upsert_points(qdrant_points)
        if result is None:
            logger.error("Failed to upsert points to Qdrant")
            
    except Exception as e:
        logger.error(f"Error processing batch: {e}", exc_info=True)


def main():
    """Main entry point for the script."""
    args = parse_args()
    
    logger.info("Starting document loading process")
    logger.info(f"Settings: docs_dir={args.docs_dir}, default_roles={args.default_roles}, "
                f"recreate_collection={args.recreate_collection}, batch_size={args.batch_size}")
    
    # Check if Qdrant manager is available
    if qdrant_manager is None:
        logger.error("Qdrant manager is not available. Please check the connection to Qdrant.")
        sys.exit(1)
        
    # Initialize document processor
    processor = DocumentProcessor(
        chunk_size=args.chunk_size,
        chunk_overlap=args.chunk_overlap
    )
    
    # Initialize embedding model
    try:
        embedding_model = get_embedding_model()
        logger.info(f"Using embedding model: {settings.OPENAI_EMBEDDING_MODEL_NAME or settings.HUGGINGFACE_EMBEDDING_MODEL_NAME}")
    except Exception as e:
        logger.error(f"Failed to initialize embedding model: {e}", exc_info=True)
        sys.exit(1)
    
    # Determine vector size
    model_name = settings.OPENAI_EMBEDDING_MODEL_NAME or settings.HUGGINGFACE_EMBEDDING_MODEL_NAME or ""
    vector_size = get_vector_size(model_name)
    logger.info(f"Using vector size: {vector_size} for model: {model_name}")
    
    # Handle collection
    if args.recreate_collection:
        logger.warning("Recreating collection. This will delete all existing data!")
        delete_success = qdrant_manager.delete_collection()
        if not delete_success:
            logger.warning("Failed to delete collection or collection did not exist.")
    
    # Ensure collection exists
    try:
        qdrant_manager.ensure_collection_exists(vector_size=vector_size)
        logger.info(f"Collection '{settings.QDRANT_COLLECTION_NAME}' is ready for ingestion.")
    except Exception as e:
        logger.error(f"Failed to ensure collection exists: {e}", exc_info=True)
        sys.exit(1)
    
    # Parse default roles
    default_roles = [role.strip() for role in args.default_roles.split(',') if role.strip()]
    logger.info(f"Using default roles: {default_roles}")
    
    # Process documents
    docs_dir = Path(args.docs_dir)
    if not docs_dir.exists() or not docs_dir.is_dir():
        logger.error(f"Documents directory '{docs_dir}' does not exist or is not a directory.")
        sys.exit(1)
    
    start_time = time.time()
    total_files, total_chunks = process_documents(
        docs_dir=docs_dir,
        default_roles=default_roles,
        processor=processor,
        embedding_model=embedding_model,
        batch_size=args.batch_size
    )
    
    # Log completion
    elapsed_time = time.time() - start_time
    logger.info(f"Document ingestion complete.")
    logger.info(f"Processed {total_files} files and uploaded {total_chunks} chunks in {elapsed_time:.1f} seconds.")
    logger.info(f"Average processing time: {elapsed_time/max(total_files, 1):.2f} seconds per file.")


if __name__ == "__main__":
    main() 