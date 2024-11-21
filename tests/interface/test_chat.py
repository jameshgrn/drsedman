#!/usr/bin/env python3
"""Script to test chatbot with embedded PDFs."""

import os
import logging
from pathlib import Path
from src.core.vectordb import VectorDB
from src.interface.bot import Bot
from src.interface.chat import Chat
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='Test chatbot with embedded PDFs')
    parser.add_argument('--db-path', default='mccode.db', help='Path to vector database')
    parser.add_argument('--test-queries', nargs='+', default=[
        "What is MLX?",
        "How does MLX compare to PyTorch?",
        "What are the key features of MLX?",
        "How can I get started with MLX?"
    ], help='Test queries to run')
    args = parser.parse_args()
    
    # Check database exists
    if not os.path.exists(args.db_path):
        raise FileNotFoundError(f"Database not found: {args.db_path}")
    
    # Initialize bot
    db = VectorDB(args.db_path, use_persistent=True)
    chat = Chat(
        name="Dr. Carl McCode",
        role="Ontological Anarchist",
        system_prompt="You are Dr. Carl McCode, ready to help with MLX questions."
    )
    
    bot = Bot(
        name="Dr. Carl McCode",
        role="Ontological Anarchist",
        db=db,
        chat=chat
    )
    
    try:
        # Run test queries
        for query in args.test_queries:
            logging.info(f"\nQuery: {query}")
            response = "".join(list(bot.get_response(query)))
            logging.info(f"Response: {response}\n")
            
        # Log some stats
        doc_count = db.get_document_count()
        emb_count = db.get_embedding_count()
        logging.info(f"Database contains {doc_count} documents with {emb_count} embeddings")
        
    finally:
        db.close()

if __name__ == '__main__':
    main() 