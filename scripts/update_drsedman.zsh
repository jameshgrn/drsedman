#!/usr/bin/env zsh

set -euo pipefail

# Get project root directory
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..

# Default paths
PDF_DIR="${1:-"${PROJECT_ROOT}/data/pdfs"}"
GEMINI_OUTPUT="${PROJECT_ROOT}/gemini_output"
DB_PATH="${PROJECT_ROOT}/data/embeddings.db"

# Print header
echo "\n=== SAND-RAG Update Pipeline ==="
echo "📂 Paths:"
echo "  📁 PDFs: ${PDF_DIR}"
echo "  📁 Output: ${GEMINI_OUTPUT}"
echo "  🗄️  Database: ${DB_PATH}\n"

# Parse arguments
RETRY_FLAG=""
if [[ "${2:-}" == "--retry" ]]; then
    RETRY_FLAG="--retry-failed"
    echo "🔄 Retry mode enabled - will reprocess existing files"
fi

# Validate required directories exist
if [[ ! -d "${PDF_DIR}" ]]; then
    echo "❌ Error: PDF directory not found: ${PDF_DIR}"
    echo "Please ensure PDFs are in data/pdfs directory"
    exit 1
fi

# Create output directories if they don't exist
mkdir -p "${GEMINI_OUTPUT}"
mkdir -p "$(dirname "${DB_PATH}")"

# Set up Python environment
export PYTHONPATH="${PROJECT_ROOT}:${PYTHONPATH:-}"

echo "🔍 Processing PDFs..."
python3 "${PROJECT_ROOT}/src/core/gemini.py" \
    --pdf-dir "${PDF_DIR}" \
    --output-dir "${GEMINI_OUTPUT}" \
    ${RETRY_FLAG}

echo "\n🔄 Updating embeddings..."
python3 -c "
from src.core.processor import process_batch
from src.core.vectordb import VectorDB
import os
import json

db = VectorDB('${DB_PATH}', use_persistent=True)
output_dir = '${GEMINI_OUTPUT}'

try:
    for file in os.listdir(output_dir):
        if file.endswith('_gemini.jsonl'):
            with open(os.path.join(output_dir, file), 'r') as f:
                content = [line.strip() for line in f if line.strip()]
                process_batch(content, db, file)
    print('Successfully processed all files')
finally:
    db.close()
"

echo "\n✅ Update complete!"
echo "📊 Summary:"
echo "  → Database location: ${DB_PATH}\n" 