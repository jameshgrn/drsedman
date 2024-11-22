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

# Validate required directories exist
if [[ ! -d "${PDF_DIR}" ]]; then
    echo "❌ Error: PDF directory not found: ${PDF_DIR}"
    echo "Please ensure PDFs are in data/pdfs directory"
    exit 1
fi

if [[ ! -d "${GEMINI_OUTPUT}" ]]; then
    echo "❌ Error: Gemini output directory not found: ${GEMINI_OUTPUT}"
    echo "Please run setup script first to initialize directories"
    exit 1
fi

if [[ ! -d "$(dirname "${DB_PATH}")" ]]; then
    echo "❌ Error: Database directory not found: $(dirname "${DB_PATH}")"
    echo "Please run setup script first to initialize directories"
    exit 1
fi

echo "🔍 Checking for new PDFs..."
new_pdfs=0
for pdf in "${PDF_DIR}"/*.pdf; do
    # Skip if no PDFs found
    [[ -e "$pdf" ]] || { echo "ℹ️  No PDFs found in ${PDF_DIR}"; continue; }
    
    # Handle filenames with spaces
    base_name=$(basename "${pdf}")
    jsonl_path="${GEMINI_OUTPUT}/${base_name%.*}_gemini.jsonl"
    
    if [[ ! -f "${jsonl_path}" ]]; then
        if (( new_pdfs == 0 )); then
            echo "\n📄 New PDFs to process:"
        fi
        echo "  → ${base_name}"
        ((new_pdfs++))
        # Process just this PDF - quote paths to handle spaces
        "${SCRIPT_DIR}/run_gemini_processing.zsh" "${pdf}" "${GEMINI_OUTPUT}"
    fi
done

if (( new_pdfs == 0 )); then
    echo "✅ No new PDFs to process"
fi

echo "\n🔄 Updating embeddings..."
"${SCRIPT_DIR}/process_and_embed.zsh"

echo "\n✅ Update complete!"
echo "📊 Summary:"
echo "  → Processed ${new_pdfs} new PDFs"
echo "  → Database location: ${DB_PATH}\n" 