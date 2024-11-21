# DrSedman

A geoscience document analysis system that uses Google's Gemini API to extract structured information from scientific papers, focusing on geomorphology and sedimentology. Based on [vegaluisjose/mlx-rag](https://github.com/vegaluisjose/mlx-rag), extended with Gemini API for PDF processing, DuckDB for embeddings and enhanced visualization.

## Features

- PDF Processing with Gemini API
  - Structured information extraction
  - Automatic metadata parsing
  - Research findings identification
  - Relationship mapping
- Beautiful Output Formats
  - Rich console display
  - HTML export with styling
  - Structured JSON storage
- Vector Database Integration
  - MLX embeddings
  - DuckDB storage
  - Similarity search
- Interactive Chat Interface
  - Context-aware responses
  - Research paper integration
  - Geoscience expertise

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jameshgrn/drsedman.git
cd drsedman
```

2. Set up Python environment:
```bash
pyenv install 3.10.14
pyenv local 3.10.14
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
poetry install
```

4. Set up credentials:
```bash
cp config/gemini_credentials_example.json config/gemini_credentials.json
# Edit config/gemini_credentials.json with your API key
```

## Usage

### Process PDFs
```bash
# Process all PDFs in a directory
./scripts/run_gemini_processing.zsh data/pdfs gemini_output

# Retry failed processing
./scripts/run_gemini_processing.zsh data/pdfs gemini_output --retry-failed
```

### View Results
```bash
# View a random processed file
./scripts/view_gemini.sh

# View a specific file
./scripts/view_gemini.sh --file gemini_output/paper_gemini.jsonl

# Save as HTML
./scripts/view_gemini.sh --save-html
```

### Create Embeddings
```bash
# Create vector embeddings from processed PDFs
./scripts/process_and_embed.zsh
```

### Chat Interface
```bash
./scripts/chat.zsh
```

## Development

```bash
# Run tests
make test

# Run linter
make lint

# Format code
make format

# Type checking
make mypy

# Run coverage
make coverage
```

## Architecture

See [architecture.md](docs/architecture.md) for detailed system design.

## Contributing

See [CONTRIBUTING.md](docs/CONTRIBUTING.md) for development guidelines.

## Current Database Stats

The system has processed approximately 750 academic papers in geoscience, extracting:
- 6,465 research findings
- 2,849 methodology entries
- 2,672 identified relationships

## License

Copyright 2024 James Hooker Gearon

Licensed under the Apache License, Version 2.0. See [LICENSE](LICENSE) for details.

## Acknowledgments

This project is based on [vegaluisjose/mlx-rag](https://github.com/vegaluisjose/mlx-rag), with significant extensions for geoscience document analysis including Gemini API integration, structured information extraction, and enhanced visualization capabilities.