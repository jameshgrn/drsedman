#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from typing import Dict, Any

console = Console()

def format_metadata(metadata: Dict[Any, Any]) -> Panel:
    """Format metadata into a nice panel."""
    table = Table(show_header=False, box=None)
    table.add_column("Key", style="blue")
    table.add_column("Value", style="white")
    
    # Add metadata fields
    for key, value in metadata.items():
        if key != 'source_file':  # Skip source_file as it's in the title
            table.add_row(key, str(value))
            
    return Panel(table, title="📋 Metadata", border_style="blue")

def format_gemini_entry(entry: Dict[Any, Any]) -> None:
    """Format a single Gemini output entry with nice formatting."""
    try:
        # Extract the content and metadata
        content = json.loads(entry['content'])  # Parse the JSON string
        metadata = entry['metadata']
        
        # Display metadata
        console.print(format_metadata(metadata))
        console.print()
        
        # Format the structured content nicely
        if 'metadata' in content:
            # Paper metadata section
            paper_md = "## Paper Information\n"
            meta = content['metadata']
            paper_md += f"**Title**: {meta.get('title', 'N/A')}\n"
            paper_md += f"**Authors**: {', '.join(a.get('name', '') for a in meta.get('authors', []))}\n"
            if meta.get('journal'):
                paper_md += f"**Journal**: {meta['journal'].get('name', 'N/A')}\n"
            paper_md += f"**Year**: {meta.get('year', 'N/A')}\n"
            console.print(Panel(Markdown(paper_md), title="📚 Paper Details", border_style="green"))
            console.print()

        if 'study' in content:
            # Study details section
            study = content['study']
            study_md = "## Study Details\n"
            if study.get('location'):
                loc = study['location']
                study_md += f"**Location**: {loc.get('name', 'N/A')}\n"
                study_md += f"**Scale**: {loc.get('scale', 'N/A')}\n"
            if study.get('objectives'):
                study_md += "\n**Objectives**:\n" + "\n".join(f"- {obj}" for obj in study['objectives'])
            console.print(Panel(Markdown(study_md), title="🔍 Study Information", border_style="yellow"))
            console.print()

        if 'findings' in content:
            # Key findings section
            findings_md = "## Key Findings\n"
            for finding in content['findings']:
                findings_md += f"\n- **{finding.get('statement', 'N/A')}**"
                if finding.get('evidence'):
                    findings_md += f"\n  *Evidence*: {finding['evidence']}"
            console.print(Panel(Markdown(findings_md), title="💡 Findings", border_style="magenta"))
            console.print()

    except KeyError as e:
        console.print(f"[red]Error: Missing required field {e}[/red]")
    except json.JSONDecodeError:
        console.print("[red]Error: Invalid JSON content[/red]")
    except Exception as e:
        console.print(f"[red]Error formatting entry: {str(e)}[/red]")
    
    console.print("=" * 80 + "\n")

def process_gemini_file(file_path: str) -> None:
    """Process a Gemini JSONL file and display its contents."""
    path = Path(file_path)
    
    console.print(f"\n[bold purple]Processing: {path.name}[/bold purple]\n")
    
    try:
        with open(path, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    format_gemini_entry(entry)
                except json.JSONDecodeError:
                    console.print(f"[red]Error decoding JSON line: {line}[/red]")
    except FileNotFoundError:
        console.print(f"[red]File not found: {file_path}[/red]")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        console.print("[red]Usage: format_gemini.py <path_to_jsonl>[/red]")
        sys.exit(1)
    
    process_gemini_file(sys.argv[1]) 