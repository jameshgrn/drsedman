import pytest
from pathlib import Path
import json
from src.tools.save_gemini_html import save_gemini_to_html

@pytest.fixture
def sample_jsonl(tmp_path):
    """Create a sample JSONL file for testing."""
    test_file = tmp_path / "test_gemini.jsonl"
    entry = {
        'content': '''{
            "metadata": {"title": "Test Paper"},
            "study": {"objectives": ["Test objective"]},
            "findings": [{"statement": "Test finding"}]
        }''',
        'metadata': {'summary_type': 'comprehensive'}
    }
    
    with open(test_file, 'w') as f:
        f.write(json.dumps(entry))
    
    return test_file

def test_save_gemini_to_html(sample_jsonl, tmp_path):
    output_dir = tmp_path / "output"
    save_gemini_to_html(str(sample_jsonl), output_dir)
    
    # Check that output file exists
    output_file = output_dir / "test_gemini_formatted.html"
    assert output_file.exists()
    
    # Check content
    content = output_file.read_text()
    assert "Test Paper" in content
    assert "Test finding" in content
    assert "background-color: #1a1a1a" in content  # Check styling

def test_save_gemini_to_html_invalid_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        save_gemini_to_html("nonexistent.jsonl", tmp_path)

def test_save_gemini_to_html_invalid_json(tmp_path):
    bad_file = tmp_path / "bad.jsonl"
    bad_file.write_text("invalid json")
    
    output_dir = tmp_path / "output"
    save_gemini_to_html(str(bad_file), output_dir)
    
    # Should create output file even with errors
    output_file = output_dir / "bad_formatted.html"
    assert output_file.exists()
    assert "Error" in output_file.read_text() 