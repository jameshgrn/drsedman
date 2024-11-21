import pytest
from src.interface.bot import Bot
from src.core.vectordb import VectorDB
import tempfile
import os
import logging
import json
from typing import Generator

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
            
            # Add test data about sediment transport
            test_content = {
                "statement": "Sediment transport in rivers is controlled by flow velocity and grain size",
                "evidence": "Laboratory flume experiments",
                "confidence": "high",
                "source": "test.pdf"
            }
            
            db.ingest(
                content=json.dumps(test_content),
                source="test.pdf",
                summary_type="finding"
            )
            
            yield db
            
        finally:
            if db is not None:
                db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

@pytest.fixture
def test_bot(test_db):
    """Create test bot instance."""
    return Bot(
        name="Dr. Sedman",
        role="Sedimentologist",
        model_name="meta-llama/Llama-3.2-3B-Instruct",
        db=test_db
    )

def test_bot_initialization(test_bot):
    """Test bot initialization."""
    assert test_bot.name == "Dr. Sedman"
    assert test_bot.role == "Sedimentologist"
    assert test_bot.model is not None
    assert test_bot.tokenizer is not None
    assert test_bot.min_similarity == 0.6

def test_bot_response(test_bot):
    """Test bot response generation."""
    query = "What do you know about sediment transport?"
    response = test_bot.get_response(query)
    
    # Check response format
    assert response is not None
    assert isinstance(response, (str, Generator))
    assert "<STOP>" in str(response)
    assert "[" in str(response) and "]" in str(response)  # Has citation

def test_bot_no_context(test_bot):
    """Test bot response when no relevant context found."""
    query = "What is quantum mechanics?"
    response = test_bot.get_response(query)
    
    assert "Based on the available sources" in str(response)
    assert "<STOP>" in str(response)