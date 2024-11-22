#!/bin/zsh

set -euo pipefail

# Get absolute paths
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..
PDF_DIR="${PROJECT_ROOT}/data/pdfs"

# Create a Python script for fuzzy matching
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << 'PYTHON'
import os
from pathlib import Path
from difflib import SequenceMatcher
import hashlib
from collections import defaultdict
import argparse

def get_file_hash(filepath):
    """Get SHA-256 hash of file contents."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clean_filename(name):
    """Clean filename for better matching."""
    # Remove common prefixes/suffixes
    name = name.lower()
    name = name.replace('(pdf)', '')
    name = name.replace('.pdf', '')
    # Remove special characters
    name = ''.join(c for c in name if c.isalnum() or c.isspace())
    # Remove extra spaces
    return ' '.join(name.split())

def find_duplicates(pdf_dir, similarity_threshold=0.85):
    """Find duplicate PDFs using fuzzy matching and content hashing."""
    pdf_dir = Path(pdf_dir)
    pdfs = list(pdf_dir.glob('*.pdf'))
    
    # First pass: group by content hash
    hash_groups = defaultdict(list)
    print("\nChecking file contents...")
    for pdf in pdfs:
        file_hash = get_file_hash(pdf)
        hash_groups[file_hash].append(pdf)
    
    # Find exact duplicates (same content)
    exact_dupes = {k: v for k, v in hash_groups.items() if len(v) > 1}
    
    # Second pass: check filenames for similar files
    print("\nChecking filenames...")
    similar_files = defaultdict(list)
    processed_files = set()
    
    for i, pdf1 in enumerate(pdfs):
        if pdf1 in processed_files:
            continue
            
        name1 = clean_filename(pdf1.name)
        group = [pdf1]
        
        for pdf2 in pdfs[i+1:]:
            if pdf2 in processed_files:
                continue
                
            name2 = clean_filename(pdf2.name)
            similarity = SequenceMatcher(None, name1, name2).ratio()
            
            if similarity >= similarity_threshold:
                group.append(pdf2)
                processed_files.add(pdf2)
        
        if len(group) > 1:
            similar_files[pdf1].extend(group[1:])
        
    return exact_dupes, similar_files

def main():
    parser = argparse.ArgumentParser(description='Find and remove duplicate PDFs')
    parser.add_argument('pdf_dir', help='Directory containing PDFs')
    parser.add_argument('--remove', action='store_true', help='Remove duplicate files')
    parser.add_argument('--threshold', type=float, default=0.85, 
                       help='Filename similarity threshold (0-1)')
    args = parser.parse_args()
    
    exact_dupes, similar_files = find_duplicates(args.pdf_dir, args.threshold)
    
    # Report findings
    if exact_dupes:
        print("\nExact duplicates (same content):")
        for hash_val, files in exact_dupes.items():
            print(f"\nDuplicate group:")
            for f in files:
                print(f"  {f.name}")
    
    if similar_files:
        print("\nSimilar filenames:")
        for original, dupes in similar_files.items():
            print(f"\nPossible duplicates of {original.name}:")
            for f in dupes:
                print(f"  {f.name}")
    
    if not exact_dupes and not similar_files:
        print("\nNo duplicates found!")
        return
    
    # Remove duplicates if requested
    if args.remove:
        print("\nRemoving duplicates...")
        removed = 0
        
        # Remove exact duplicates (keep first one)
        for files in exact_dupes.values():
            for f in files[1:]:
                f.unlink()
                print(f"Removed exact duplicate: {f.name}")
                removed += 1
        
        # Remove similar files (keep first one)
        for dupes in similar_files.values():
            for f in dupes:
                f.unlink()
                print(f"Removed similar file: {f.name}")
                removed += 1
        
        print(f"\nRemoved {removed} duplicate files")
    else:
        print("\nRun with --remove to delete duplicate files")

if __name__ == '__main__':
    main()
PYTHON

# Run the script
echo "Checking for duplicate PDFs in ${PDF_DIR}..."
python3 "$TMP_SCRIPT" "${PDF_DIR}"

# Clean up
rm "$TMP_SCRIPT" 