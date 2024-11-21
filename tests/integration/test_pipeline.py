import pytest
from src.core.processor import process_pdf

def test_process_pdf(test_pdf):
    """Test PDF processing."""
    # Process PDF
    chunks = list(process_pdf(test_pdf))
    
    # Debug output
    print(f"\nDebug: Processing PDF: {test_pdf}")
    print(f"Debug: Got {len(chunks)} chunks")
    if chunks:
        print(f"Debug: First chunk: {chunks[0][:100]}")
    
    # Verify chunks
    assert len(chunks) > 0
    assert isinstance(chunks[0], str)
    assert len(chunks[0]) > 0  # Should have content