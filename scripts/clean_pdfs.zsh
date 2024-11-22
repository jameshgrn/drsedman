#!/bin/zsh

set -euo pipefail

# Get absolute paths
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..
PDF_DIR="${PROJECT_ROOT}/data/pdfs"

# Print usage info
echo "\n=== PDF Duplicate Cleaner ==="
echo "📂 PDF Directory: ${PDF_DIR}"
echo "ℹ️  Usage:"
echo "  • ./clean_pdfs.zsh              - Show duplicates without removing"
echo "  • ./clean_pdfs.zsh --remove     - Remove duplicates"
echo "  • ./clean_pdfs.zsh --threshold 0.75 --remove  - More aggressive matching"

# Create a Python script for fuzzy matching
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << 'PYTHON'
import os
from pathlib import Path
from difflib import SequenceMatcher
import hashlib
from collections import defaultdict
import argparse
import re

def get_file_hash(filepath):
    """Get SHA-256 hash of file contents."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def clean_filename(name):
    """Clean filename for better matching."""
    # Remove common prefixes/suffixes and file extension
    name = name.lower()
    name = re.sub(r'\(pdf\)', '', name, flags=re.IGNORECASE)
    name = re.sub(r'\.pdf$', '', name, flags=re.IGNORECASE)
    
    # Remove year patterns
    name = re.sub(r'\b\d{4}\b', '', name)
    
    # Remove common prefixes
    name = re.sub(r'^(the|a|an)\s+', '', name)
    
    # Remove parentheses and their contents
    name = re.sub(r'\([^)]*\)', '', name)
    
    # Remove special characters and extra whitespace
    name = re.sub(r'[^\w\s]', ' ', name)
    name = ' '.join(name.split())
    
    # Remove common words
    stop_words = {'and', 'or', 'the', 'in', 'on', 'at', 'to', 'for', 'of', 'with'}
    words = [w for w in name.split() if w not in stop_words]
    
    return ' '.join(words)

def find_duplicates(pdf_dir, similarity_threshold=0.85):
    """Find duplicate PDFs using fuzzy matching and content hashing."""
    pdf_dir = Path(pdf_dir)
    pdfs = list(pdf_dir.glob('*.pdf'))
    
    print(f"\n🔍 Found {len(pdfs)} PDF files")
    
    # First pass: group by content hash
    hash_groups = defaultdict(list)
    print("\n📊 Checking file contents...")
    for pdf in pdfs:
        file_hash = get_file_hash(pdf)
        hash_groups[file_hash].append(pdf)
    
    # Find exact duplicates (same content)
    exact_dupes = {k: v for k, v in hash_groups.items() if len(v) > 1}
    
    # Second pass: check filenames for similar files
    print("\n📝 Analyzing filenames...")
    similar_files = defaultdict(list)
    processed_files = set()
    
    for i, pdf1 in enumerate(pdfs):
        if pdf1 in processed_files:
            continue
            
        name1 = clean_filename(pdf1.name)
        if not name1.strip():  # Skip if filename is empty after cleaning
            continue
            
        group = [pdf1]
        
        for pdf2 in pdfs[i+1:]:
            if pdf2 in processed_files:
                continue
                
            name2 = clean_filename(pdf2.name)
            if not name2.strip():
                continue
                
            # Calculate similarity
            similarity = SequenceMatcher(None, name1, name2).ratio()
            
            if similarity >= similarity_threshold:
                print(f"\n🔍 Found similar files ({similarity:.2f}):")
                print(f"  1. {pdf1.name}")
                print(f"  2. {pdf2.name}")
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
        print("\n🔍 Exact duplicates (same content):")
        for hash_val, files in exact_dupes.items():
            print(f"\n  Duplicate group:")
            for i, f in enumerate(files, 1):
                print(f"    {i}. {f.name}")
                if i == 1:
                    print("       ↳ This file will be kept")
                else:
                    print("       ↳ This file will be removed")
    
    if similar_files:
        print("\n🔍 Similar filenames:")
        for original, dupes in similar_files.items():
            print(f"\n  Group based on: {original.name}")
            print(f"    → Will keep this file")
            for f in dupes:
                print(f"    → Will remove: {f.name}")
                print(f"      Clean name comparison:")
                print(f"        1. {clean_filename(original.name)}")
                print(f"        2. {clean_filename(f.name)}")
    
    if not exact_dupes and not similar_files:
        print("\n✅ No duplicates found!")
        return
    
    # Remove duplicates if requested
    if args.remove:
        print("\n🗑️  Removing duplicates...")
        removed = 0
        skipped = 0
        
        # Remove exact duplicates (keep first one)
        for files in exact_dupes.values():
            for f in files[1:]:
                try:
                    if f.exists():  # Check if file still exists
                        f.unlink()
                        print(f"  ✓ Removed exact duplicate: {f.name}")
                        removed += 1
                    else:
                        print(f"  ⚠️  Already removed: {f.name}")
                        skipped += 1
                except Exception as e:
                    print(f"  ❌ Error removing {f.name}: {str(e)}")
        
        # Remove similar files (keep first one)
        for dupes in similar_files.values():
            for f in dupes:
                try:
                    if f.exists():  # Check if file still exists
                        f.unlink()
                        print(f"  ✓ Removed similar file: {f.name}")
                        removed += 1
                    else:
                        print(f"  ⚠️  Already removed: {f.name}")
                        skipped += 1
                except Exception as e:
                    print(f"  ❌ Error removing {f.name}: {str(e)}")
        
        print(f"\n✅ Summary:")
        print(f"  • Removed: {removed} files")
        print(f"  • Skipped: {skipped} files (already removed)")
    else:
        total = sum(len(files)-1 for files in exact_dupes.values()) + \
                sum(len(dupes) for dupes in similar_files.values())
        print(f"\n⚠️  Found {total} duplicate files")
        print("Run with --remove to delete duplicate files")

if __name__ == '__main__':
    main()
PYTHON

# Pass command line arguments to the Python script
if [[ $# -gt 0 ]]; then
    python3 "$TMP_SCRIPT" "${PDF_DIR}" "$@"
else
    python3 "$TMP_SCRIPT" "${PDF_DIR}"
fi

# Clean up
rm "$TMP_SCRIPT" 