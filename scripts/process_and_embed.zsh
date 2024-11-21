#!/usr/bin/env zsh

set -euo pipefail  # Stricter error handling

# Add error handling function
handle_error() {
    echo "Error occurred in process_and_embed.zsh"
    echo "Line: $1"
    echo "Exit code: $2"
    exit 1
}

trap 'handle_error ${LINENO} $?' ERR

# Get project root directory
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..

# Default settings
PDF_DIR=${1:-"${PROJECT_ROOT}/data/pdfs"}
OUTPUT_DIR=${2:-"${PROJECT_ROOT}/gemini_output"}
DB_PATH=${3:-"${PROJECT_ROOT}/data/embeddings.db"}
LOOKUP_PATH="${PROJECT_ROOT}/data/lookups.json"

# Debug: Print paths
echo "Script directory: $SCRIPT_DIR"
echo "Project root: $PROJECT_ROOT"
echo "PDF directory: $PDF_DIR"
echo "Output directory: $OUTPUT_DIR"
echo "Database path: $DB_PATH"
echo "Lookup path: $LOOKUP_PATH"

# Check directories
if [[ ! -d "$PDF_DIR" ]]; then
    echo "Error: PDF directory not found: $PDF_DIR"
    exit 1
fi

# Create output directories
mkdir -p "$OUTPUT_DIR"
mkdir -p "$(dirname "$DB_PATH")"
mkdir -p "$(dirname "$LOOKUP_PATH")"

# Count PDFs
PDF_COUNT=$(ls -1 "$PDF_DIR"/*.pdf 2>/dev/null | wc -l)
echo "\nFound $PDF_COUNT PDFs to process"

# Initialize PYTHONPATH if not set
export PYTHONPATH=${PYTHONPATH:-""}

# Add project root to PYTHONPATH
if [[ -z "$PYTHONPATH" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

# Run embedding process
cd "$PROJECT_ROOT"  # Change to project root
python -u scripts/process_and_embed.py \
    --input-dir "$OUTPUT_DIR" \
    --db-path "$DB_PATH" \
    --lookup-path "$LOOKUP_PATH"

echo "\nPipeline complete!"
echo "- Check $OUTPUT_DIR for Gemini summaries"
echo "- Check $DB_PATH for vector embeddings"
echo "- Check $LOOKUP_PATH for metadata" 