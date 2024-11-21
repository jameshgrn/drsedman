import pytest
import logging
import time
from src.core.processor import chunk_generator, get_processed_files, update_progress
import tempfile
import os

logging.basicConfig(level=logging.INFO)

def test_chunk_generator_simple():
    """Test the chunk generator with a very simple input"""
    logging.info("Starting simple chunk generator test...")
    start_time = time.time()
    
    # Single sentence test
    text = "Test."
    chunks = list(chunk_generator(text, max_chunk_size=10, overlap=0))
    assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
    assert chunks[0] == "Test.", f"Expected 'Test.', got '{chunks[0]}'"
    
    elapsed = time.time() - start_time
    logging.info(f"Simple chunk test completed in {elapsed:.2f} seconds")

def test_chunk_generator_multiple():
    """Test the chunk generator with multiple sentences"""
    logging.info("Starting multiple sentence chunk test...")
    start_time = time.time()
    
    # Multiple sentence test with reasonable chunks
    text = "One. Two. Three."
    chunks = list(chunk_generator(text, max_chunk_size=8, overlap=0))
    
    logging.info(f"Generated chunks: {chunks}")
    assert len(chunks) > 1, "Should generate multiple chunks"
    assert all(len(chunk) <= 8 for chunk in chunks), "Chunks exceed max size"
    
    elapsed = time.time() - start_time
    logging.info(f"Multiple chunk test completed in {elapsed:.2f} seconds")

def test_progress_file_none():
    """Test progress file handling with None"""
    logging.info("Testing progress file with None...")
    result = get_processed_files(None)
    assert isinstance(result, dict), "Should return dict even with None input"
    assert len(result) == 0, "Should return empty dict"

def test_progress_file_missing():
    """Test progress file handling with non-existent file"""
    logging.info("Testing progress file with missing file...")
    with tempfile.NamedTemporaryFile(suffix='.json', delete=True) as tmp:
        path = tmp.name  # File is deleted immediately
    result = get_processed_files(path)
    assert isinstance(result, dict), "Should return dict for missing file"
    assert len(result) == 0, "Should return empty dict"

def test_progress_file_existing():
    """Test progress file handling with existing file"""
    logging.info("Testing progress file with existing file...")
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp:
        tmp.write('{"test.pdf": 5}')
        tmp.flush()
        
        try:
            result = get_processed_files(tmp.name)
            assert result == {"test.pdf": 5}, "Should read existing progress"
        finally:
            os.unlink(tmp.name)

@pytest.mark.parametrize("test_input,expected", [
    ("", []),  # Empty input
    ("Small.", ["Small."]),  # Single small chunk
    ("One. Two.", ["One.", "Two."]),  # Multiple chunks
])
def test_chunk_generator_cases(test_input, expected):
    """Test the chunk generator with various inputs"""
    logging.info(f"Testing chunk generator with input: {test_input}")
    start_time = time.time()
    
    chunks = list(chunk_generator(test_input, max_chunk_size=10, overlap=0))
    assert chunks == expected, f"Expected {expected}, got {chunks}"
    
    elapsed = time.time() - start_time
    logging.info(f"Test completed in {elapsed:.2f} seconds")

def test_chunk_generator_invalid_params():
    """Test the chunk generator with invalid parameters"""
    logging.info("Testing chunk generator invalid parameters...")
    start_time = time.time()
    
    with pytest.raises(ValueError):
        list(chunk_generator("Test", max_chunk_size=0, overlap=0))
    with pytest.raises(ValueError):
        list(chunk_generator("Test", max_chunk_size=5, overlap=-1))
    with pytest.raises(ValueError):
        list(chunk_generator("Test", max_chunk_size=5, overlap=6))
    
    elapsed = time.time() - start_time
    logging.info(f"Invalid params test completed in {elapsed:.2f} seconds")

def test_chunk_generator_sentence_boundaries():
    """Test that chunks respect sentence boundaries"""
    logging.info("Testing chunk generator sentence boundaries...")
    start_time = time.time()
    
    text = "First. Second. Third."
    chunks = list(chunk_generator(text, max_chunk_size=10, overlap=0))
    
    logging.info(f"Sentence boundary chunks: {chunks}")
    assert all(chunk.endswith(('.', '!', '?', '\n')) for chunk in chunks), \
        "Chunks should end at sentence boundaries"
    
    elapsed = time.time() - start_time
    logging.info(f"Sentence boundaries test completed in {elapsed:.2f} seconds")