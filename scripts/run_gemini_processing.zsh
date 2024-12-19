#!/bin/zsh

set -euo pipefail

# Get absolute paths
SCRIPT_DIR=${0:A:h}
PROJECT_ROOT=${SCRIPT_DIR}/..

# Process PDFs with Gemini API
# Usage: ./run_gemini_processing.zsh [pdf_path] [output_dir]

# Get absolute paths and handle spaces/special chars in filenames
PDF_PATH="${1:-"${PROJECT_ROOT}/data/pdfs"}"  # Quote to handle spaces
OUTPUT_DIR="${2:-"${PROJECT_ROOT}/gemini_output"}"
ENV_FILE="${PROJECT_ROOT}/.env"

# Print key info
echo "\n=== Gemini Processing Pipeline ==="
echo "📁 Input: ${PDF_PATH}"
echo "📁 Output: ${OUTPUT_DIR}"
echo "⚙️  Config: ${ENV_FILE}\n"

# Check for .env file and contents
if [[ ! -f "${ENV_FILE}" ]]; then
    echo "❌ Error: .env file not found at: ${ENV_FILE}"
    echo "Please create one with your Gemini API key:"
    echo "GEMINI_API_KEY=your_api_key_here"
    exit 1
fi

# Initialize PYTHONPATH if not set
export PYTHONPATH=${PYTHONPATH:-""}

# Add project root to PYTHONPATH
if [[ -z "$PYTHONPATH" ]]; then
    export PYTHONPATH="$PROJECT_ROOT"
else
    export PYTHONPATH="$PROJECT_ROOT:$PYTHONPATH"
fi

# Create a Python script with proper escaping
TMP_SCRIPT=$(mktemp)
cat > "$TMP_SCRIPT" << 'PYTHON'
from src.core.gemini import setup_gemini, process_pdf
from dotenv import load_dotenv
import sys
import os
import json
import signal

# Handle broken pipe error
signal.signal(signal.SIGPIPE, signal.SIG_DFL)

def process_single_pdf(pdf_path, output_dir, env_file):
    """Process a single PDF with error handling."""
    try:
        # Load API key from .env with explicit path
        load_dotenv(env_file)
        api_key = os.getenv('GEMINI_API_KEY')
        print(f"🔑 API Key: {'[FOUND]' if api_key else '[NOT FOUND]'}")
        
        if not api_key:
            raise ValueError(f"GEMINI_API_KEY not found in {env_file}")
        
        # Setup Gemini API
        setup_gemini()
        
        # Process the PDF
        print(f"\n📄 Processing: {os.path.basename(pdf_path)}")
        results = process_pdf(pdf_path)
        
        if results:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save results
            base_name = os.path.basename(pdf_path)
            output_name = base_name.replace('.pdf', '_gemini.jsonl')
            output_path = os.path.join(output_dir, output_name)
            
            with open(output_path, 'w') as f:
                for result in results:
                    json.dump(result, f)
                    f.write('\n')
            print(f"✅ Success: Generated {output_name}")
            return True
        else:
            print(f"⚠️  Warning: No results generated for {os.path.basename(pdf_path)}")
            return False
            
    except BrokenPipeError:
        # Just exit for broken pipe
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error processing {os.path.basename(pdf_path)}: {str(e)}", file=sys.stderr)
        return False

def main():
    try:
        # Get paths from environment
        pdf_path = os.environ['PDF_PATH']
        output_dir = os.environ['OUTPUT_DIR']
        env_file = os.environ['ENV_FILE']
        
        success = process_single_pdf(pdf_path, output_dir, env_file)
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n⚠️  Processing interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
PYTHON

# Export paths as environment variables
export PDF_PATH
export OUTPUT_DIR
export ENV_FILE

# Run the Python script and handle errors
if ! python3 -u "$TMP_SCRIPT"; then
    echo "⚠️  Processing failed for: ${PDF_PATH}"
fi

# Clean up
rm "$TMP_SCRIPT"