#!/bin/zsh

# Directory containing Gemini output files
GEMINI_DIR="gemini_output"

# Get a random file from the directory
random_file=$(ls "$GEMINI_DIR"/*_gemini.jsonl | sort -R | head -n 1)

# Check if we found a file
if [[ -z "$random_file" ]]; then
    echo "No Gemini output files found in $GEMINI_DIR"
    exit 1
fi

# Run the Python formatter on the random file
python3 src/tools/format_gemini.py "$random_file" 