#!/bin/zsh

set -euo pipefail  # Stricter error handling

# Add error handling function
handle_error() {
    echo "Error occurred in run_gemini_processing.zsh"
    echo "Line: $1"
    echo "Exit code: $2"
    exit 1
}

trap 'handle_error ${LINENO} $?' ERR

# Process PDFs with Gemini API
# Usage: ./run_gemini_processing.zsh [pdf_dir] [output_dir] [--retry-failed]

# Get absolute paths
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..
PDF_DIR=${1:-"${PROJECT_ROOT}/data/pdfs"}
OUTPUT_DIR=${2:-"${PROJECT_ROOT}/gemini_output"}

# Check for retry flag - handle case when $3 is not set
RETRY_FLAG=""
if [ $# -ge 3 ] && [ "$3" = "--retry-failed" ]; then
    RETRY_FLAG="--retry-failed"
fi

# Initialize PYTHONPATH if not set
export PYTHONPATH=${PYTHONPATH:-""}

# Add project root to PYTHONPATH
if [[ -z "$PYTHONPATH" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

# Print key info
echo "Starting Gemini processing pipeline..."
echo "PDF Directory: ${PDF_DIR##*/}"  # Show only last component
echo "Output Directory: ${OUTPUT_DIR##*/}"

# Check directory exists
if [[ ! -d "$PDF_DIR" ]]; then
    echo "Error: Directory not found: $PDF_DIR"
    exit 1
fi

# Get PDF count quietly
PDF_COUNT=$(find "$PDF_DIR" -name "*.pdf" -type f | wc -l | tr -d ' ')
echo "Found $PDF_COUNT PDFs to process"

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Run Gemini processing
cd "$PROJECT_ROOT"
python3 -m src.core.gemini \
    --pdf-dir "$PDF_DIR" \
    --output-dir "$OUTPUT_DIR" \
    ${RETRY_FLAG:+"$RETRY_FLAG"}

echo "\nPipeline complete!"
echo "- Check ${OUTPUT_DIR##*/} for Gemini summaries"