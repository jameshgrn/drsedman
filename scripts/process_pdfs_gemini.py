#!/usr/bin/env python3
"""Script to process PDFs using Google's Gemini API."""

import os
import sys
import logging
from pathlib import Path
import google.generativeai as genai
from typing import List, Dict, Any, Generator, Union, Optional
from dotenv import load_dotenv
import json
import concurrent.futures
from tqdm import tqdm
import time
import argparse
import ssl
import gc
from datetime import datetime

# Define prompts and summary types
prompts = [
    """Extract structured information from this geoscience paper. Format as JSON with this schema:

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
]

# Map prompts to summary types
summary_types = {
    0: 'comprehensive'  # Single comprehensive summary type
}

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

# At the top with other constants
MAX_FILE_SIZE_MB = 5  # Conservative default based on Gemini's limits

def setup_gemini() -> None:
    """Initialize Gemini API using key from environment."""
    load_dotenv()
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment")
    genai.configure(api_key=api_key)

def process_pdf(pdf_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Process PDF using Gemini's document AI."""
    results = []
    
    try:
        # Initialize Gemini model with better error handling
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
        except Exception as e:
            logging.error(f"Failed to initialize Gemini model: {str(e)}")
            return []

        # Add file validation
        if not validate_pdf(pdf_path):
            return []

        # Process with prompts using improved retry logic
        for i, prompt in enumerate(prompts):
            result = process_with_retry(model, pdf_path, prompt, max_retries=3)
            if result:
                results.append({
                    'content': result,
                    'metadata': {
                        'source_file': str(pdf_path),
                        'summary_type': summary_types[i],
                        'processed_at': datetime.now().isoformat()
                    }
                })

        return results

    except Exception as e:
        logging.error(f"Fatal error processing {pdf_path}: {str(e)}")
        return results

def validate_pdf(pdf_path: Union[str, Path]) -> bool:
    """Validate PDF file before processing."""
    try:
        if not os.path.exists(pdf_path):
            logging.error(f"File not found: {pdf_path}")
            return False
            
        file_size = os.path.getsize(pdf_path)
        if file_size == 0:
            logging.warning(f"Empty PDF: {pdf_path}")
            return False
            
        # File size limit in bytes
        MAX_FILE_SIZE = MAX_FILE_SIZE_MB * 1024 * 1024
        if file_size > MAX_FILE_SIZE:
            logging.warning(
                f"PDF too large for Gemini API ({file_size/1024/1024:.1f}MB > {MAX_FILE_SIZE_MB}MB): {pdf_path}"
            )
            return False
            
        # Minimum size check
        if file_size < 1000:  # Less than 1KB
            logging.warning(f"PDF too small to be valid: {pdf_path}")
            return False

        return True
        
    except Exception as e:
        logging.error(f"PDF validation failed: {str(e)}")
        return False

def validate_jsonl(jsonl_path: Path) -> bool:
    """Validate if JSONL file exists and contains valid content."""
    try:
        if not jsonl_path.exists():
            return False
            
        if jsonl_path.stat().st_size == 0:
            logging.warning(f"Empty JSONL file: {jsonl_path}")
            return False
            
        # Check if file contains valid JSON
        with open(jsonl_path) as f:
            for line_num, line in enumerate(f, 1):
                try:
                    data = json.loads(line)
                    # Verify required fields
                    if not all(k in data for k in ['content', 'metadata']):
                        logging.warning(f"Missing required fields in {jsonl_path}, line {line_num}")
                        return False
                    # Verify content is valid JSON
                    content = json.loads(data['content'])
                    if not all(k in content for k in ['metadata', 'study', 'findings']):
                        logging.warning(f"Invalid content structure in {jsonl_path}, line {line_num}")
                        return False
                except json.JSONDecodeError:
                    logging.warning(f"Invalid JSON in {jsonl_path}, line {line_num}")
                    return False
                except Exception as e:
                    logging.warning(f"Error validating {jsonl_path}, line {line_num}: {e}")
                    return False
        return True
        
    except Exception as e:
        logging.error(f"Failed to validate {jsonl_path}: {e}")
        return False

def process_pdfs_parallel(
    pdf_dir: Union[str, Path],
    output_dir: Union[str, Path],
    max_workers: int = 4,
    retry_failed: bool = True
) -> None:
    """Process multiple PDFs in parallel."""
    # Convert to absolute paths
    pdf_dir_path = Path(pdf_dir).resolve()
    output_dir_path = Path(output_dir).resolve()
    output_dir_path.mkdir(exist_ok=True)
    
    # Get list of PDFs
    pdfs = list(pdf_dir_path.glob('*.pdf'))
    if not pdfs:
        logging.error(f"No PDFs found in {pdf_dir_path}")
        return
        
    logging.info(f"Found {len(pdfs)} PDFs")
    
    # Track processing status
    to_process = []
    for pdf in pdfs:
        jsonl_path = output_dir_path / f"{pdf.stem}_gemini.jsonl"
        
        # Check if we need to process this PDF
        if retry_failed or not validate_jsonl(jsonl_path):
            to_process.append(pdf)
            if jsonl_path.exists():
                logging.info(f"Will reprocess {pdf.name} (invalid or incomplete JSONL)")
            else:
                logging.info(f"Will process {pdf.name} (new PDF)")
        else:
            logging.info(f"Skipping {pdf.name} (valid JSONL exists)")
    
    if not to_process:
        logging.info("No PDFs need processing")
        return
        
    logging.info(f"Processing {len(to_process)} PDFs")
    
    # Process in batches
    batch_size = 3
    max_concurrent = 1
    
    for i in range(0, len(to_process), batch_size):
        batch = to_process[i:i + batch_size]
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_concurrent) as executor:
                future_to_pdf = {
                    executor.submit(process_pdf, pdf): pdf 
                    for pdf in batch
                }
                
                for future in tqdm(
                    concurrent.futures.as_completed(future_to_pdf),
                    total=len(batch),
                    desc="Processing PDFs"
                ):
                    pdf = future_to_pdf[future]
                    try:
                        results = future.result()
                        if results:
                            output_path = output_dir_path / f"{pdf.stem}_gemini.jsonl"
                            with open(output_path, 'w') as f:
                                for result in results:
                                    json.dump(result, f)
                                    f.write('\n')
                            logging.info(f"Successfully processed {pdf.name}")
                        else:
                            logging.error(f"No results generated for {pdf.name}")
                            
                    except Exception as e:
                        logging.error(f"Failed to process {pdf.name}: {str(e)}")
                        
        except Exception as e:
            logging.error(f"Batch processing failed: {str(e)}")
            
        finally:
            gc.collect()
            time.sleep(10)

def process_with_retry(
    model: genai.GenerativeModel,
    pdf_path: Union[str, Path],
    prompt: str,
    max_retries: int = 3
) -> Optional[str]:
    """Process PDF with retry logic."""
    for attempt in range(max_retries):
        pdf_file = None
        try:
            # Upload with shorter timeout
            pdf_file = genai.upload_file(str(pdf_path))
            
            # Generate content with more specific error handling
            try:
                response = model.generate_content(
                    [prompt, pdf_file],
                    generation_config=genai.GenerationConfig(
                        temperature=0.1,
                        candidate_count=1,
                        max_output_tokens=25000,
                        top_p=0.8,  # Added for more focused output
                        top_k=40    # Added for more focused output
                    ),
                    safety_settings=[
                        {
                            "category": "HARM_CATEGORY_DANGEROUS",
                            "threshold": "BLOCK_NONE"
                        }
                    ]
                )
            except Exception as e:
                logging.error(f"Generation failed for {pdf_path}, attempt {attempt + 1}: {str(e)}")
                if "rate limit" in str(e).lower():
                    wait = (attempt + 1) * 30  # Longer wait for rate limits
                    time.sleep(wait)
                continue
            
            # Check if response is empty
            if not response.text:
                logging.warning(f"Empty response for {pdf_path}, attempt {attempt + 1}")
                continue
            
            # Clean and validate JSON
            content = response.text.strip()
            try:
                # Remove any markdown code block markers
                if content.startswith('```json'):
                    content = content[7:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                # Validate JSON structure
                parsed = json.loads(content)
                if not all(k in parsed for k in ['metadata', 'study', 'findings']):
                    logging.warning(f"Missing required fields in response for {pdf_path}, attempt {attempt + 1}")
                    continue
                    
                # Validate specific fields
                if not parsed['metadata'].get('title'):
                    logging.warning(f"Missing title in metadata for {pdf_path}, attempt {attempt + 1}")
                    continue
                    
                if not parsed['findings']:
                    logging.warning(f"No findings extracted from {pdf_path}, attempt {attempt + 1}")
                    continue
                
                return content
                
            except json.JSONDecodeError as e:
                logging.warning(f"Invalid JSON response for {pdf_path}, attempt {attempt + 1}: {str(e)}")
                logging.debug(f"Response content: {content[:500]}...")
                continue
                
        except (ssl.SSLError, TimeoutError) as e:
            wait = (attempt + 1) * 5
            logging.warning(f"Network error on attempt {attempt + 1} for {pdf_path}: {str(e)}")
            if attempt < max_retries - 1:
                logging.info(f"Waiting {wait}s before retry...")
                time.sleep(wait)
            continue
            
        except Exception as e:
            logging.error(f"Processing failed for {pdf_path}: {str(e)}")
            break
            
        finally:
            if pdf_file:
                try:
                    pdf_file.delete()
                except:
                    pass
                pdf_file = None
    
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Process PDFs using Gemini API')
    parser.add_argument('--pdf-dir', default='data/pdfs', 
                       help='Directory containing PDFs')
    parser.add_argument('--output-dir', default='gemini_output',
                       help='Output directory for JSONL files')
    parser.add_argument('--max-workers', type=int, default=4,
                       help='Maximum number of parallel workers')
    parser.add_argument('--retry-failed', action='store_true',
                       help='Retry previously processed PDFs')
    args = parser.parse_args()

    # Setup
    setup_gemini()
    
    # Process PDFs in parallel
    process_pdfs_parallel(
        pdf_dir=args.pdf_dir,
        output_dir=args.output_dir,
        max_workers=args.max_workers,
        retry_failed=args.retry_failed
    ) 