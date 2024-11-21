import pytest
import warnings
import tempfile
import os
from src.core.model import Model
from src.core.vectordb import VectorDB
import logging
import fitz

logging.basicConfig(level=logging.INFO)

def pytest_configure(config):
    """Configure pytest."""
    # Filter out SWIG-related warnings
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="builtin type .* has no __module__ attribute"
    )

@pytest.fixture(scope="session")
def test_model():
    """Create model fixture for tests."""
    try:
        model = Model()
        return model
    except Exception as e:
        pytest.skip(f"Model initialization failed: {str(e)}")

@pytest.fixture
def test_db():
    """Create a temporary test database."""
    logging.info("Setting up test database...")
    db = None
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        try:
            # Create new database
            db = VectorDB(tmp.name, use_persistent=True)
            
            # Add test data
            db.ingest(
                content="Test content",
                source="test.txt",
                summary_type="test"
            )
            
            yield db
            
        finally:
            if db is not None:
                db.close()
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            logging.info("Cleaned up test database")

@pytest.fixture
def test_pdf():
    """Create a sample PDF file for testing."""
    # Copy a real PDF from data/pdfs to a temp location
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        # Copy the first PDF we find in data/pdfs
        pdf_dir = os.path.join("data", "pdfs")
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith('.pdf')]
        if not pdf_files:
            pytest.skip("No test PDFs found in data/pdfs")
        
        # Copy the first PDF
        src_pdf = os.path.join(pdf_dir, pdf_files[0])
        with open(src_pdf, 'rb') as src:
            tmp.write(src.read())
        
        yield tmp.name
        
        # Cleanup
        os.unlink(tmp.name)

@pytest.fixture
def sample_pdf():
    """Create a sample PDF file for testing"""
    logging.info("Creating sample PDF...")
    content = """
    This is a test PDF file.
    It contains multiple sentences.
    We will use it to test our processing pipeline.
    """
    with tempfile.NamedTemporaryFile(suffix='.pdf', mode='w', delete=False) as tmp:
        tmp.write(content)
        tmp.flush()
        yield tmp.name
        os.unlink(tmp.name)
        logging.info("Cleaned up sample PDF") 