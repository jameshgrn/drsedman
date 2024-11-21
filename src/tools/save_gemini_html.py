#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from typing import Dict, Any, Optional
import format_gemini  # Import our existing formatter

def save_gemini_to_html(input_path: str, output_dir: Optional[Path] = None) -> None:
    """Save Gemini output as formatted HTML with preserved styling."""
    path = Path(input_path)
    
    # Create output directory if not specified
    if output_dir is None:
        output_dir = Path('formatted_output')
    output_dir.mkdir(exist_ok=True)
    
    # Create HTML console for saving
    html_console = Console(record=True, force_terminal=True)
    
    try:
        with open(path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    # Pass the HTML console to the formatter
                    format_gemini.format_gemini_entry(entry, console=html_console)
                except json.JSONDecodeError:
                    html_console.print(f"[red]Error decoding JSON line: {line}[/red]")
        
        # Generate HTML with styles
        html_content = '''
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {
                    background-color: #1a1a1a;
                    color: #ffffff;
                    font-family: monospace;
                    padding: 20px;
                    max-width: 1200px;
                    margin: 0 auto;
                }
                pre {
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
            </style>
        </head>
        <body>
            <pre style="font-family: monospace; padding: 20px;">
        '''
        html_content += html_console.export_html(inline_styles=True)
        html_content += '''
            </pre>
        </body>
        </html>
        '''
        
        # Save to file
        output_path = output_dir / f"{path.stem}_formatted.html"
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Formatted output saved to: {output_path}")
        
    except Exception as e:
        print(f"Error processing file: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: save_gemini_html.py <path_to_jsonl>")
        sys.exit(1)
    
    save_gemini_to_html(sys.argv[1]) 