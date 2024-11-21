import pymupdf4llm
from typing import List, Generator, Optional, Iterator
from .vectordb import VectorDB
import os
import logging
import uuid
import json
import psutil
import time
from .pdf_utils import process_pdf  # Updated import

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

MAX_MEMORY_USAGE = 80 * 1024 * 1024 * 1024  # 80 GB in bytes

def get_processed_files(progress_file: Optional[str]) -> dict:
    """Get the progress of processed files from a JSON file."""
    if progress_file and os.path.exists(progress_file):
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

def update_progress(progress_file: Optional[str], filename: str, chunks_processed: int) -> None:
    """Update the progress of processed files in a JSON file."""
    if not progress_file:  # Early return if no progress file
        return
    progress = get_processed_files(progress_file)
    progress[filename] = chunks_processed
    with open(progress_file, 'w') as f:
        json.dump(progress, f)

def chunk_generator(md_text: str, max_chunk_size: int, overlap: int) -> Generator[str, None, None]:
    """Generate chunks from markdown text with specified size and overlap."""
    if not md_text:  # Add early return for empty input
        return
        
    if max_chunk_size <= 0:
        raise ValueError("max_chunk_size must be positive")
        
    if overlap < 0:
        raise ValueError("overlap must be non-negative")
        
    if overlap >= max_chunk_size:
        raise ValueError("overlap must be less than max_chunk_size")
    
    # Split into sentences first
    sentences = []
    current_sentence = []
    
    for char in md_text:
        current_sentence.append(char)
        if char in '.!?\n':
            sentence = ''.join(current_sentence).strip()
            if sentence:  # Only add non-empty sentences
                sentences.append(sentence)
            current_sentence = []
    
    # Add any remaining text as a sentence
    if current_sentence:
        sentence = ''.join(current_sentence).strip()
        if sentence:
            sentences.append(sentence)
    
    # Now yield each sentence separately
    for sentence in sentences:
        if len(sentence) > max_chunk_size:
            # If a single sentence is too long, split it at max_chunk_size
            for i in range(0, len(sentence), max_chunk_size):
                yield sentence[i:i + max_chunk_size].strip()
        else:
            yield sentence

def process_batch(batch: List[str], db: VectorDB, pdf_path: str) -> None:
    """Process a batch of text chunks and store them in the database."""
    try:
        for chunk in batch:
            db.ingest(content=chunk, source=pdf_path)
    except Exception as e:
        logging.error(f"Error processing batch from {pdf_path}: {e}")
        raise

# ... rest of the file remains the same but with Optional[str] for progress_file ... 