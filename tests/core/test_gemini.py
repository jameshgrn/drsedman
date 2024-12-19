"""Tests for Gemini processing functionality."""

import pytest
from pathlib import Path
from src.core.gemini import process_pdf, setup_gemini

def test_setup_gemini(monkeypatch):
    """Test Gemini setup with mock API key."""
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
    setup_gemini()  # Should not raise error

def test_process_pdf(tmp_path, monkeypatch):
    """Test PDF processing with mock Gemini model."""
    # Create test PDF
    test_pdf = tmp_path / "test.pdf"
    test_pdf.write_bytes(b"%PDF-1.4\n%EOF\n")  # Minimal valid PDF with EOF marker
    
    # Mock Gemini API and response
    class MockResponse:
        text = '{"content": "test content", "metadata": {"test": "value"}}'
    
    class MockModel:
        def generate_content(self, *args, **kwargs):
            return MockResponse()
    
    class MockGenerationConfig:
        def __init__(self, **kwargs):
            self.temperature = kwargs.get('temperature', 0.1)
            self.candidate_count = kwargs.get('candidate_count', 1)
            self.max_output_tokens = kwargs.get('max_output_tokens', 2048)
            self.top_p = kwargs.get('top_p', 0.8)
            self.top_k = kwargs.get('top_k', 40)
    
    class MockGenAI:
        def __init__(self):
            self.GenerationConfig = MockGenerationConfig
            
        def GenerativeModel(self, *args):
            return MockModel()
        
        def configure(self, *args, **kwargs):
            pass
            
        def upload_file(self, *args, **kwargs):
            return "mock_file"
    
    mock_genai = MockGenAI()
    
    # Apply mocks
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
    monkeypatch.setattr("google.generativeai", mock_genai)
    monkeypatch.setattr("src.core.gemini.genai", mock_genai)  # Mock the imported instance
    
    # Setup Gemini (this should now use our mock)
    setup_gemini()
    
    # Make test file larger than minimum size
    with open(test_pdf, 'wb') as f:
        f.write(b"%PDF-1.4\n" + b"x" * 2000 + b"\n%EOF\n")
    
    results = process_pdf(test_pdf)
    assert isinstance(results, dict)
    assert 'content' in results
    assert 'metadata' in results