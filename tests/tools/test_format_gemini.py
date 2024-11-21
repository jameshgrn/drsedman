import pytest
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from src.tools.format_gemini import (
    format_metadata, 
    format_authors,
    format_journal_info,
    format_location_info,
    format_method_info,
    format_data_info,
    format_gemini_entry
)

@pytest.fixture
def sample_entry():
    return {
        'content': '''{
            "metadata": {
                "title": "Test Paper",
                "authors": [
                    {"name": "John Doe", "affiliation": "Test University"}
                ],
                "year": "2024",
                "journal": {
                    "name": "Test Journal",
                    "volume": "1",
                    "pages": "1-10"
                }
            },
            "study": {
                "location": {
                    "name": "Test Site",
                    "scale": "local",
                    "coordinates": {"lat": 10.0, "lon": 20.0}
                },
                "objectives": ["Test objective"],
                "methods": [{
                    "name": "Test method",
                    "type": "field",
                    "description": "Test description",
                    "tools": ["Tool1"]
                }]
            },
            "findings": [{
                "statement": "Test finding",
                "type": "observation",
                "evidence": "Test evidence",
                "confidence": "high"
            }]
        }''',
        'metadata': {
            'source_file': 'test.pdf',
            'summary_type': 'comprehensive'
        }
    }

@pytest.fixture
def test_console():
    return Console(force_terminal=True)

def test_format_metadata(sample_entry):
    result = format_metadata(sample_entry['metadata'])
    assert isinstance(result, Panel)
    console = Console(force_terminal=True)
    with console.capture() as capture:
        console.print(result)
    output = capture.get()
    assert "comprehensive" in output

def test_format_authors():
    authors = [
        {"name": "John Doe", "affiliation": "Test University"},
        {"name": "Jane Doe", "affiliation": None}
    ]
    result = format_authors(authors)
    assert "John Doe (Test University)" in result
    assert "Jane Doe" in result

def test_format_journal_info():
    journal = {
        "name": "Test Journal",
        "volume": "1",
        "pages": "1-10"
    }
    result = format_journal_info(journal)
    assert "Test Journal" in result
    assert "1-10" in result

def test_format_location_info():
    location = {
        "name": "Test Site",
        "scale": "local",
        "coordinates": {"lat": 10.0, "lon": 20.0}
    }
    result = format_location_info(location)
    assert "Test Site" in result
    assert "10.0°" in result

def test_format_method_info():
    method = {
        "name": "Test method",
        "type": "field",
        "description": "Test description",
        "tools": ["Tool1"]
    }
    result = format_method_info(method)
    assert "Test method" in result
    assert "Tool1" in result

def test_format_data_info():
    data = {
        "parameter": "height",
        "value": "10",
        "units": "m",
        "uncertainty": "±1"
    }
    result = format_data_info(data)
    assert "height" in result
    assert "±1" in result

def test_format_gemini_entry(sample_entry, test_console):
    # This should not raise any exceptions
    format_gemini_entry(sample_entry, console=test_console)

def test_format_gemini_entry_invalid_json(test_console):
    bad_entry = {
        'content': 'invalid json',
        'metadata': {'summary_type': 'comprehensive'}
    }
    # This should handle the error gracefully
    format_gemini_entry(bad_entry, console=test_console) 