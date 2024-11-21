"""
MLX-RAG: A RAG implementation using MLX
"""

from .core import VectorDB, process_pdf, chunk_generator
from .interface import Bot, Chat

__version__ = "0.1.0"
__all__ = [
    'VectorDB',
    'process_pdf',
    'chunk_generator',
    'Bot',
    'Chat',
]
