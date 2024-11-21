#!/usr/bin/env zsh

set -euo pipefail

# Get project root directory
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..

# Default paths
PDF_DIR=${1:-"${PROJECT_ROOT}/data/pdfs"}
GEMINI_OUTPUT="${PROJECT_ROOT}/gemini_output"
DB_PATH="${PROJECT_ROOT}/data/embeddings.db"

echo "Starting SAND-RAG update pipeline..."

# 1. Find new PDFs (not yet processed)
echo "\nChecking for new PDFs..."
for pdf in $PDF_DIR/*.pdf; do
    jsonl_path="${GEMINI_OUTPUT}/$(basename ${pdf%.*})_gemini.jsonl"
    if [[ ! -f "$jsonl_path" ]]; then
        echo "Found new PDF: $(basename $pdf)"
        # Process just this PDF
        ./scripts/run_gemini_processing.zsh "$pdf" "$GEMINI_OUTPUT"
    fi
done

# 2. Find new JSONL files (not yet embedded)
echo "\nChecking for new embeddings..."
./scripts/process_and_embed.zsh

echo "\nUpdate complete! Database preserved at $DB_PATH" 