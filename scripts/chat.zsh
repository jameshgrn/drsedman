#!/usr/bin/env zsh

set -euo pipefail  # Stricter error handling

# Add error handling
handle_error() {
    echo "Error occurred in mccode.zsh"
    echo "Line: $1"
    echo "Exit code: $2"
    exit 1
}

trap 'handle_error ${LINENO} $?' ERR

# Get project root directory
PROJECT_ROOT=${0:A:h}/..  # Get absolute path of script's parent's parent

# Default to Gemini embeddings database
DB_PATH=${1:-"embeddings.db"}
DEBUG=${DEBUG:-false}  # Add DEBUG variable with default

# Check database exists
if [[ ! -f "$DB_PATH" ]]; then
    echo "Error: Database not found: $DB_PATH"
    echo "Run ./process_and_embed.zsh first to create embeddings"
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

# Run the bot
python3 -c "
from src.interface.bot import Bot
from src.interface.chat import Chat
from src.core.vectordb import VectorDB
import json
import logging
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

try:
    # Initialize chat and bot
    chat = Chat(
        name='Dr. Sedman',
        role='Sedimentologist',
        system_prompt='Dr. Sedman is ready to help.',
        history_file='.chat_history.json'
    )
    
    db = VectorDB('$DB_PATH', use_persistent=True)
    bot = Bot(
        name='Dr. Sedman',
        role='Sedimentologist',
        db=db,
        chat=chat
    )
    
    # Start conversation loop
    print(f'\nDr. Sedman is ready to chat! (Ctrl+C to exit)\n')
    
    while True:
        try:
            print('You: ', end='', flush=True)
            query = sys.stdin.readline().strip()
            if not query:
                continue
            
            # Check for exit command
            if query.lower() in ['exit', 'quit', 'bye']:
                print('\nGoodbye!\n')
                break
                
            print('\nDr. Sedman:', end=' ', flush=True)
            for token in bot.get_response(query):
                print(token, end='', flush=True)
            print('\n')
            
        except (KeyboardInterrupt, EOFError):
            print('\nGoodbye!\n')
            break
        except Exception as e:
            logging.error(f'Error: {str(e)}')
            if ${DEBUG}:  # Use string substitution
                raise
            
finally:
    if 'db' in locals():
        db.close()
" 