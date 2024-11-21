from .processor import (
    chunk_generator,
    get_processed_files,
    update_progress,
    process_pdf,
    process_batch
)
from .vectordb import VectorDB
import warnings

# Suppress SWIG-related warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, 
                      message="builtin type .* has no __module__ attribute")

__all__ = [
    'chunk_generator',
    'get_processed_files',
    'update_progress',
    'process_pdf',
    'process_batch',
    'VectorDB'
]
