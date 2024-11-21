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
    test_pdf.write_bytes(b"%PDF-1.4\n")  # Minimal valid PDF
    
    # Mock Gemini response
    monkeypatch.setenv('GEMINI_API_KEY', 'test_key')
    results = process_pdf(str(test_pdf))
    assert isinstance(results, list) 