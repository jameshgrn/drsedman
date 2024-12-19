"""DrSedman: Geoscience Document Analysis System."""

__version__ = "0.1.0"

from .core import (
    VectorDB,
    process_pdf,
    chunk_generator,
    Model,
    process_pdf_gemini,
    setup_gemini
)

__all__ = [
    'VectorDB',
    'process_pdf',
    'chunk_generator',
    'Model',
    'process_pdf_gemini',
    'setup_gemini'
]
