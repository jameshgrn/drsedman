import pytest
import tempfile
import os
import json
from src.core.model import Model
from src.core.vectordb import VectorDB
import logging

@pytest.fixture(scope="module")
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

def test_end_to_end_pipeline(test_db, test_model):
    """Test full pipeline from ingestion to search."""
    # 1. Create test data
    test_findings = [
        {
            "statement": "River channels migrate laterally over time",
            "evidence": "Satellite imagery analysis",
            "confidence": "high"
        },
        {
            "statement": "Sediment transport increases during floods",
            "evidence": "Field measurements",
            "confidence": "high"
        }
    ]
    
    # 2. Ingest test data
    for i, finding in enumerate(test_findings):
        test_db.ingest(
            content=json.dumps(finding),
            source=f"test_{i}.pdf",
            summary_type="finding"
        )
    
    # 3. Search for relevant content
    results = test_db.search("channel migration", top_k=2)
    
    # 4. Verify results
    assert len(results) > 0
    assert results[0]['similarity'] > 0.5
    first_result = json.loads(results[0]['content'])
    assert "channel" in first_result['statement'].lower()
    
    # 5. Check embedding consistency
    query_embedding = test_model.run(["channel migration"])[0]
    assert len(query_embedding) == 1024

def test_database_persistence(test_db):
    """Test database maintains data between operations."""
    # 1. Initial count
    initial_count = test_db.get_document_count()
    
    # 2. Add new document
    test_db.ingest(
        content=json.dumps({
            "statement": "New finding about rivers",
            "evidence": "Test data"
        }),
        source="test.pdf",
        summary_type="finding"
    )
    
    # 3. Verify count increased
    new_count = test_db.get_document_count()
    assert new_count == initial_count + 1
    
    # 4. Check embedding was created
    assert test_db.get_embedding_count() == new_count