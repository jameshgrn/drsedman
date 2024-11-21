#!/bin/zsh

# Directory containing Gemini output files
GEMINI_DIR="gemini_output"
SAVE_HTML=false
SPECIFIC_FILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --save-html)
            SAVE_HTML=true
            shift
            ;;
        --file)
            SPECIFIC_FILE="$2"
            shift 2
            ;;
        *)
            shift
            ;;
    esac
done

# Use specific file or get random one
if [[ -n "$SPECIFIC_FILE" ]]; then
    file_to_process="$SPECIFIC_FILE"
else
    file_to_process=$(ls "$GEMINI_DIR"/*_gemini.jsonl | sort -R | head -n 1)
fi

# Check if we found a file
if [[ -z "$file_to_process" ]]; then
    echo "No Gemini output files found in $GEMINI_DIR"
    exit 1
fi

# Run the Python formatter on the file
python3 src/tools/format_gemini.py "$file_to_process"

# Optionally save as HTML
if [[ "$SAVE_HTML" = true ]]; then
    python3 src/tools/save_gemini_html.py "$file_to_process"
fi 