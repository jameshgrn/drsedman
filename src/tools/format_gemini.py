#!/usr/bin/env python3
import json
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from rich.table import Table
from typing import Dict, Any, Optional

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

def format_authors(authors: list) -> str:
    """Format author information with affiliations."""
    author_strings = []
    for author in authors:
        author_str = author.get('name', 'N/A')
        if author.get('affiliation'):
            author_str += f" ({author['affiliation']})"
        author_strings.append(author_str)
    return ', '.join(author_strings)

def format_journal_info(journal: dict) -> str:
    """Format journal information."""
    info = []
    if journal.get('name'):
        info.append(f"Name: {journal['name']}")
    if journal.get('volume'):
        info.append(f"Volume: {journal['volume']}")
    if journal.get('pages'):
        info.append(f"Pages: {journal['pages']}")
    return '\n    '.join(info) if info else 'N/A'

def format_location_info(location: dict) -> str:
    """Format location information."""
    info = []
    if location.get('name'):
        info.append(f"Name: {location['name']}")
    if location.get('scale'):
        info.append(f"Scale: {location['scale']}")
    
    if location.get('coordinates'):
        coords = location['coordinates']
        lat = coords.get('lat', 'N/A')
        lon = coords.get('lon', 'N/A')
        info.append(f"Coordinates: {lat}°, {lon}°")
    
    if location.get('time_period'):
        period = location['time_period']
        start = period.get('start', 'N/A')
        end = period.get('end', 'N/A')
        info.append(f"Time Period: {start} to {end}")
    
    return '\n    '.join(info) if info else 'N/A'

def format_method_info(method: dict) -> str:
    """Format method information."""
    info = [
        f"Name: {method.get('name', 'N/A')}",
        f"Type: {method.get('type', 'N/A')}",
        f"Description: {method.get('description', 'N/A')}"
    ]
    if method.get('tools'):
        info.append(f"Tools: {', '.join(method['tools'])}")
    return '\n    '.join(info)

def format_data_info(data: dict) -> str:
    """Format measurement data information."""
    info = []
    if data.get('parameter'):
        info.append(f"Parameter: {data['parameter']}")
    if data.get('value'):
        info.append(f"Value: {data['value']}")
    if data.get('units'):
        info.append(f"Units: {data['units']}")
    if data.get('uncertainty'):
        info.append(f"Uncertainty: {data['uncertainty']}")
    return '\n      '.join(info) if info else 'N/A'

def format_gemini_entry(entry: Dict[Any, Any], console: Optional[Console] = None) -> None:
    """Format a single Gemini output entry with nice formatting.
    
    Args:
        entry: The Gemini entry to format
        console: Optional console to use for output (defaults to global console)
    """
    # Use provided console or fall back to global
    output_console = console or globals()['console']
    
    try:
        content = json.loads(entry['content'])
        metadata = entry['metadata']
        
        # Display metadata
        output_console.print(format_metadata(metadata))
        output_console.print()
        
        # Paper Metadata Section
        if 'metadata' in content:
            meta = content['metadata']
            paper_md = "## Paper Metadata\n\n"
            paper_md += f"**Title**: {meta.get('title', 'N/A')}\n\n"
            
            paper_md += "**Authors**:\n"
            for author in meta.get('authors', []):
                paper_md += f"- Name: {author.get('name', 'N/A')}\n"
                paper_md += f"  Affiliation: {author.get('affiliation', 'N/A')}\n"
            
            paper_md += f"\n**Year**: {meta.get('year', 'N/A')}\n"
            
            if meta.get('journal'):
                paper_md += "\n**Journal Information**:\n"
                paper_md += f"    {format_journal_info(meta['journal'])}\n"
            
            paper_md += f"\n**DOI**: {meta.get('doi', 'N/A')}\n"
            
            if meta.get('keywords'):
                paper_md += f"\n**Keywords**: {', '.join(meta['keywords'])}\n"
            
            output_console.print(Panel(Markdown(paper_md), title="📚 Paper Metadata", border_style="green"))
            output_console.print()

        # Study Section
        if 'study' in content:
            study = content['study']
            study_md = "## Study Details\n\n"
            
            if study.get('location'):
                study_md += "**Location Information**:\n"
                study_md += f"    {format_location_info(study['location'])}\n\n"
            
            if study.get('objectives'):
                study_md += "**Research Objectives**:\n"
                for i, obj in enumerate(study['objectives'], 1):
                    study_md += f"{i}. {obj}\n"
                study_md += "\n"
            
            if study.get('methods'):
                study_md += "**Research Methods**:\n"
                for i, method in enumerate(study['methods'], 1):
                    study_md += f"\nMethod {i}:\n    {format_method_info(method)}\n"
            
            output_console.print(Panel(Markdown(study_md), title="🔍 Study Details", border_style="yellow"))
            output_console.print()

        # Findings Section
        if 'findings' in content:
            findings_md = "## Research Findings\n\n"
            for i, finding in enumerate(content['findings'], 1):
                findings_md += f"### Finding {i}\n"
                findings_md += f"**Statement**: {finding.get('statement', 'N/A')}\n"
                findings_md += f"**Type**: {finding.get('type', 'N/A')}\n"
                
                if finding.get('data'):
                    findings_md += "**Measurements**:\n"
                    findings_md += f"      {format_data_info(finding['data'])}\n"
                
                findings_md += f"**Evidence**: {finding.get('evidence', 'N/A')}\n"
                findings_md += f"**Confidence Level**: {finding.get('confidence', 'N/A')}\n\n"
            
            output_console.print(Panel(Markdown(findings_md), title="💡 Research Findings", border_style="magenta"))
            output_console.print()

        # Relationships Section
        if 'relationships' in content:
            rel_md = "## Identified Relationships\n\n"
            for i, rel in enumerate(content['relationships'], 1):
                rel_md += f"### Relationship {i}\n"
                rel_md += f"**Type**: {rel.get('type', 'N/A')}\n"
                rel_md += f"**Description**: {rel.get('description', 'N/A')}\n"
                rel_md += f"**Evidence**: {rel.get('evidence', 'N/A')}\n"
                rel_md += f"**Strength**: {rel.get('strength', 'N/A')}\n\n"
            
            output_console.print(Panel(Markdown(rel_md), title="🔗 Relationships", border_style="cyan"))
            output_console.print()

    except Exception as e:
        output_console.print(f"[red]Error formatting entry: {str(e)}[/red]")
    
    output_console.print("=" * 100 + "\n")

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