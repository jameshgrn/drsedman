import pytest
import tempfile
import os
import json
from src.core.model import Model
from src.core.vectordb import VectorDB

@pytest.fixture
def test_model():
    """Create model fixture for tests."""
    try:
        model = Model()
        yield model
    finally:
        pass

@pytest.fixture
def test_db():
    """Create a temporary test database."""
    db = None
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        try:
            os.unlink(tmp.name)
            db = VectorDB(tmp.name, use_persistent=True)
            yield db
        finally:
            if db is not None:
                db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def test_end_to_end_processing(test_db, test_pdf):  # Use test_pdf fixture
    """Test full pipeline from PDF to embeddings."""
    # Create test content
    test_content = {
        "statement": "Test finding about sediment transport",
        "evidence": "Experimental observation",
        "source": test_pdf
    }
    
    # Add to database
    test_db.ingest(
        content=json.dumps(test_content),  # Convert dict to JSON string
        source=test_pdf,
        summary_type="finding"
    )
    
    # Verify content was stored
    results = test_db.search("sediment transport", top_k=1)
    assert len(results) > 0
    assert results[0]['similarity'] > 0.5