#!/usr/bin/env python3
"""Script to test PDF chunking and display results."""

import os
import sys
import logging
from pathlib import Path

# Add project root to PYTHONPATH
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from src.core.pdf_utils import process_pdf
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='Test PDF chunking')
    parser.add_argument('pdf_path', help='Path to PDF file to test')
    parser.add_argument('--show-chunks', action='store_true', help='Display chunk contents')
    args = parser.parse_args()
    
    try:
        # Process PDF and get chunks
        chunks = list(process_pdf(args.pdf_path))
        logging.info(f"Generated {len(chunks)} chunks from {args.pdf_path}")
        
        # Display chunk info
        for i, chunk in enumerate(chunks, 1):
            word_count = len(chunk.split())
            logging.info(f"Chunk {i}: {word_count} words")
            if args.show_chunks:
                print(f"\n{'='*80}\nChunk {i}:\n{'='*80}")
                print(chunk)
                print(f"{'='*80}\n")
                
    except Exception as e:
        logging.error(f"Failed to process PDF: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main() 