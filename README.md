# SAND-RAG

A Retrieval-Augmented Generation (RAG) implementation specialized for sedimentology and geomorphology research. Based on [vegaluisjose/mlx-rag](https://github.com/vegaluisjose/mlx-rag), extended with Gemini API for PDF processing and DuckDB for vector storage.

## Features

- PDF processing with Google's Gemini API
- Vector embeddings using MLX
- DuckDB for vector storage
- Interactive chat interface with Dr. Sedman, a sedimentology expert

## Installation

# Clone the repository
git clone https://github.com/yourusername/mlx-rag.git
cd mlx-rag

# Install with poetry
poetry install

# Or with pip
pip install -e .

# Set up environment variables
cp .env.example .env
# Edit .env with your Gemini API key

## Usage

1. Process PDFs with Gemini:
# Process PDFs in data/pdfs directory
./scripts/run_gemini_processing.zsh data/pdfs gemini_output

2. Create embeddings:
# Create vector embeddings from processed PDFs
./scripts/process_and_embed.zsh

3. Chat with Dr. Sedman:
# Start interactive chat session
./scripts/mccode.zsh data/embeddings.db

## Project Structure

mlx-rag/
├── src/              # Source code
│   ├── core/         # Core functionality (model, vectordb)
│   ├── interface/    # User interaction (bot, chat)
│   └── utils/        # Utilities (inspection, text processing)
├── scripts/          # Command line tools
├── tests/            # Test suite
├── data/            # Data storage
│   ├── pdfs/        # Source PDFs
│   └── embeddings/  # Vector database
└── config/          # Configuration files

## Development

# Run tests
make test

# Format code
make format

# Run linter
make lint

# Clean up cache files
make clean

## Configuration

Key configuration files:
- `config/settings.yaml`: Main configuration
- `.env`: Environment variables (API keys)

## Database Stats

Current database contains:
- 6,465 findings
- 2,849 methodology entries
- 2,672 relationships
From approximately 750 academic papers in geoscience.

## License

MIT

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request