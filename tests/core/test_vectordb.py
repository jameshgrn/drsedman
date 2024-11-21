import pytest
import tempfile
import os
import json
from src.core.vectordb import VectorDB

@pytest.fixture
def test_db():
    """Create a temporary test database."""
    db = None
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        try:
            # Remove file so DuckDB can create it fresh
            os.unlink(tmp.name)
            
            # Create new database
            db = VectorDB(tmp.name, use_persistent=True)
            yield db
            
        finally:
            if db is not None:
                db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

def test_database_initialization(test_db):
    """Test database initialization."""
    assert test_db is not None
    assert test_db.conn is not None
    
    # Check tables exist
    tables = test_db.conn.execute("SHOW TABLES").fetchall()
    table_names = [t[0] for t in tables]
    assert "documents" in table_names
    assert "embeddings" in table_names

def test_document_ingestion(test_db):
    """Test document ingestion."""
    test_content = {
        "statement": "Rivers transport sediment",
        "evidence": "Field observations",
        "confidence": "high",
        "source": "test.pdf"
    }
    
    # Ingest document
    test_db.ingest(
        content=json.dumps(test_content),
        source="test.pdf",
        summary_type="finding"
    )
    
    # Verify document was stored
    docs = test_db.conn.execute("SELECT * FROM documents").fetchall()
    assert len(docs) == 1
    assert "Rivers transport sediment" in docs[0][1]  # content column
    
    # Verify embedding was created
    embeddings = test_db.conn.execute("SELECT * FROM embeddings").fetchall()
    assert len(embeddings) == 1
    assert len(embeddings[0][1]) == 1024  # embedding dimension

def test_document_search(test_db):
    """Test document search."""
    # Add test documents
    test_db.ingest(
        content=json.dumps({
            "statement": "Rivers transport sediment downstream",
            "evidence": "Field study"
        }),
        source="doc1.pdf",
        summary_type="finding"
    )
    
    test_db.ingest(
        content=json.dumps({
            "statement": "Climate affects rainfall patterns",
            "evidence": "Weather data"
        }),
        source="doc2.pdf",
        summary_type="finding"
    )
    
    # Search for relevant documents
    results = test_db.search("sediment transport", top_k=2)
    
    # Verify results
    assert len(results) > 0
    assert results[0]['similarity'] > 0.5
    assert "sediment" in json.loads(results[0]['content'])['statement'].lower() 