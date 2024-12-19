#!/usr/bin/env python3
"""Script to process PDFs using Google's Gemini API."""

import os
import logging
from pathlib import Path
import google.generativeai as genai
from typing import Dict, Any, Optional
from dotenv import load_dotenv
import json
from datetime import datetime
import gc

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# Constants
MAX_FILE_SIZE_MB = 100  # Gemini's limit is actually higher but let's be conservative

# Define prompts for extraction
EXTRACTION_PROMPT = """Extract structured information from this geoscience paper. Format as JSON with this schema:

{
    "metadata": {
        "title": "string - full title",
        "authors": [
            {
                "name": "string - full name",
                "affiliation": "string - institution or null"
            }
        ],
        "year": "string - publication year or null",
        "journal": {
            "name": "string - journal name or null",
            "volume": "string - volume number or null",
            "pages": "string - page range or null"
        },
        "doi": "string - DOI or null",
        "keywords": ["string - key terms"]
    },
    "study": {
        "location": {
            "name": "string - study area name or null",
            "coordinates": {
                "lat": "number - latitude or null",
                "lon": "number - longitude or null"
            },
            "scale": "string - local/regional/global",
            "time_period": {
                "start": "string - start date/period or null", 
                "end": "string - end date/period or null"
            }
        },
        "objectives": [
            "string - clear research goals"
        ],
        "methods": [
            {
                "name": "string - method name",
                "type": "string - field/remote_sensing/model/lab",
                "description": "string - clear description",
                "tools": ["string - equipment/software used"]
            }
        ]
    },
    "findings": [
        {
            "statement": "string - key finding",
            "type": "string - observation/measurement/interpretation",
            "data": {
                "parameter": "string - what was measured or null",
                "value": "string or number - measured value or null",
                "units": "string - measurement units or null",
                "uncertainty": "string or number - error bounds or null"
            },
            "evidence": "string - supporting evidence or null",
            "confidence": "string - high/medium/low or null"
        }
    ],
    "relationships": [
        {
            "type": "string - causal/correlation/spatial",
            "description": "string - clear description",
            "evidence": "string - supporting evidence or null",
            "strength": "string - strong/moderate/weak"
        }
    ]
}

Important:
1. Ensure all JSON is properly formatted and terminated
2. Use null for missing/unknown values
3. Include only factual information from the paper
4. Be precise with measurements and units
5. Maintain proper JSON escaping for quotes and special characters
6. Do NOT wrap the JSON in code block markers (no ```json)


Extract this information from the provided PDF:"""

def setup_gemini() -> None:
    """Initialize Gemini API using key from environment."""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    genai.configure(api_key=api_key)

def validate_pdf(pdf_path: Path) -> bool:
    """Check if PDF is valid and within size limits."""
    try:
        if not pdf_path.exists():
            logging.error(f"File not found: {pdf_path}")
            return False
            
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        if file_size_mb > MAX_FILE_SIZE_MB:
            logging.warning(f"PDF too large for processing ({file_size_mb:.1f}MB > {MAX_FILE_SIZE_MB}MB): {pdf_path.name}")
            return False
            
        if file_size_mb < 0.001:  # 1KB
            logging.warning(f"PDF too small to be valid: {pdf_path.name}")
            return False
            
        return True
        
    except Exception as e:
        logging.error(f"Error validating PDF {pdf_path.name}: {str(e)}")
        return False

def process_pdf(pdf_path: Path) -> Optional[Dict[str, Any]]:
    """Process a single PDF using Gemini's document AI."""
    try:
        # Validate PDF first
        if not validate_pdf(pdf_path):
            return None
            
        # Initialize model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Upload file directly to Gemini
        pdf_file = genai.upload_file(str(pdf_path))
        
        # Generate content with the extraction prompt
        response = model.generate_content(
            [EXTRACTION_PROMPT, pdf_file],
            generation_config=genai.GenerationConfig(
                temperature=0.1,
                candidate_count=1,
                max_output_tokens=25000,
                top_p=0.8,
                top_k=40
            ),
            safety_settings=[
                {
                    "category": "HARM_CATEGORY_DANGEROUS",
                    "threshold": "BLOCK_NONE"
                }
            ]
        )
        
        if not response.text:
            logging.error(f"No content generated for {pdf_path.name}")
            return None
            
        # Parse and validate JSON response
        content = response.text.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        result = {
            'content': content,
            'metadata': {
                'source_file': str(pdf_path),
                'processed_at': datetime.now().isoformat()
            }
        }
        
        # Validate JSON structure
        json.loads(content)  # This will raise JSONDecodeError if invalid
        return result
        
    except Exception as e:
        logging.error(f"Failed to process {pdf_path.name}: {str(e)}")
        return None
    finally:
        gc.collect()

def process_directory(pdf_dir: Path, output_dir: Path, retry_failed: bool = False) -> None:
    """Process all PDFs in a directory."""
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Get list of PDFs to process
    pdfs = list(pdf_dir.glob('*.pdf'))
    if not pdfs:
        logging.info("No PDFs found")
        return
        
    logging.info(f"Found {len(pdfs)} PDFs")
    
    # Process each PDF
    for pdf in pdfs:
        output_path = output_dir / f"{pdf.stem}_gemini.jsonl"
        
        # Skip if already processed and not retrying
        if output_path.exists() and not retry_failed:
            logging.info(f"Skipping {pdf.name} (already processed)")
            continue
            
        logging.info(f"Processing {pdf.name}")
        result = process_pdf(pdf)
        
        if result:
            with open(output_path, 'w') as f:
                json.dump(result, f)
                f.write('\n')
            logging.info(f"Successfully processed {pdf.name}")
        else:
            logging.error(f"Failed to process {pdf.name}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Process PDFs using Gemini API')
    parser.add_argument('--pdf-dir', type=Path, default='data/pdfs',
                       help='Directory containing PDFs')
    parser.add_argument('--output-dir', type=Path, default='gemini_output',
                       help='Output directory for JSONL files')
    parser.add_argument('--retry-failed', action='store_true',
                       help='Retry previously processed PDFs')
    args = parser.parse_args()
    
    setup_gemini()
    process_directory(args.pdf_dir, args.output_dir, args.retry_failed) 