import pytest
import numpy as np
from src.core.model import Model

@pytest.fixture(scope="module")
def test_model():
    """Create model fixture for tests."""
    try:
        model = Model()
        yield model
    finally:
        # No cleanup needed for model
        pass

def test_model_initialization(test_model):
    """Test model initialization."""
    assert test_model is not None
    assert test_model.model is not None
    assert test_model.tokenizer is not None
    assert test_model.embedding_size == 1024

def test_embedding_generation(test_model):
    """Test embedding generation."""
    # Test single text
    text = "Rivers transport sediment downstream"
    embedding = test_model.run([text])[0]
    
    # Check embedding properties
    assert embedding is not None
    assert len(embedding) == 1024  # Expected embedding size
    assert all(hasattr(x, '__float__') for x in embedding)  # All values are numeric

def test_batch_embedding(test_model):
    """Test batch embedding generation."""
    texts = [
        "Rivers transport sediment",
        "Climate affects rainfall",
        "Erosion shapes landscapes"
    ]
    
    embeddings = test_model.run(texts)
    
    # Check batch results
    assert len(embeddings) == len(texts)
    assert all(len(emb) == 1024 for emb in embeddings)
    
    # Check embeddings are different
    assert not np.allclose(embeddings[0], embeddings[1]) 