import logging
import fitz  # PyMuPDF
import pymupdf4llm
from typing import Dict, Any, Iterator

logging.basicConfig(level=logging.INFO)

def process_pdf(pdf_path: str, db=None) -> Iterator[str]:
    """Process PDF and yield chunks.
    
    Args:
        pdf_path: Path to PDF file
        db: Optional database instance (for compatibility)
    """
    try:
        # Extract markdown text using PyMuPDF4LLM with optimized settings
        chunks = pymupdf4llm.to_markdown(
            pdf_path,
            # Use semantic chunking
            page_chunks=True,
            # Strict table detection for better structure
            table_strategy='lines_strict',
            # Ignore small images/graphics that might break text flow
            image_size_limit=0.1,
            # Don't extract images
            write_images=False,
            # Show progress
            show_progress=True,
            # Set margins to avoid headers/footers
            margins=(72, 72, 72, 72),  # 1 inch margins
            # Force text extraction even when overlapping images
            force_text=True,
            # Detect code blocks
            ignore_code=False,
            # Extract words for better chunking
            extract_words=True,
            # Use page width of standard A4
            page_width=595
        )
        
        # Process each page's text
        for chunk in chunks:
            if isinstance(chunk, dict):
                text: str = chunk.get('text', '').strip()
                # Only yield non-empty chunks
                if text and len(text.split()) > 20:  # Minimum 20 words per chunk
                    yield text
            
    except Exception as e:
        logging.error(f"Error processing {pdf_path}: {str(e)}")
        yield ""