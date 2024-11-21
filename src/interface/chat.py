from dataclasses import dataclass, field
from typing import List, Dict, Optional, Generator
import time
import json
import logging
import re

@dataclass
class Chat:
    """Chat interface for managing conversations."""
    name: str
    role: str
    system_prompt: str
    history_file: str = ".chat_history.json"
    max_history: int = 10
    history: List[Dict[str, str]] = field(default_factory=list)
    
    def __post_init__(self):
        self.load_history()
        
    def load_history(self) -> None:
        """Load chat history from file."""
        try:
            with open(self.history_file, 'r') as f:
                self.history = json.load(f)
                if len(self.history) > self.max_history:
                    self.history = self.history[-self.max_history:]
        except (FileNotFoundError, json.JSONDecodeError):
            self.history = []
            
    def save_history(self) -> None:
        """Save chat history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history[-self.max_history:], f)
            
    def add_message(self, role: str, content: str) -> None:
        """Add a message to chat history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": str(time.time())
        }
        self.history.append(message)
        self.save_history()
        
    def clear_history(self) -> None:
        """Clear chat history."""
        self.history = []
        self.save_history()
        
    def clean_content(self, text: str) -> str:
        """Clean content for better readability."""
        # Remove figure/table references and dates
        text = re.sub(r'Fig\.\s*\d+.*?\n', '', text)
        text = re.sub(r'Table\s*\d+.*?\n', '', text)
        text = re.sub(r'\(\w+\s+\d{1,2}\s+\w+\s+\d{4}\)', '', text)
        
        # Remove page numbers and headers
        text = re.sub(r'\d+\s*$', '', text)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def get_response(self, query: str, context: Optional[str] = None) -> Generator[str, None, None]:
        """Generate response to user query."""
        # Add query to history
        self.add_message("user", query)
        
        # Generate response
        if context:
            # Extract meaningful content from sources
            source_content = []
            current_source = None
            
            for line in context.split('\n'):
                # Skip empty lines and metadata
                if not line.strip() or '(similarity:' in line:
                    continue
                    
                # Track source changes
                if line.startswith('From '):
                    current_source = line.split('From ')[-1].split()[0]
                    continue
                    
                # Clean and add content
                clean_line = self.clean_content(line)
                if clean_line and len(clean_line.split()) > 10:  # Skip very short lines
                    source_content.append((current_source, clean_line))
            
            # Build response from content
            if source_content:
                response = "Based on the available sources, "
                
                # Add unique content with citations
                seen_content = set()
                for source, content in source_content:
                    if content not in seen_content and len(content.split()) > 10:
                        # Clean up the content and make it more readable
                        clean_content = content.replace('(Source: None)', '')
                        if clean_content and len(clean_content.split()) > 10:
                            response += f"{clean_content} (Source: {source}). "
                            seen_content.add(content)
                            
                # Add follow-up prompt if appropriate
                if query.lower().startswith(('what', 'how', 'why')):
                    response += "\nWould you like to know more about any specific aspect?"
            else:
                response = "I apologize, but I couldn't find specific information about that in my sources. "
                response += "Could you try rephrasing your question or ask about a related topic?"
        else:
            response = "I apologize, but I don't have access to relevant sources to answer that question. "
            response += "Please try asking about something covered in the available documents."
            
        # Add response to history
        self.add_message("assistant", response)
        
        # Yield response tokens properly
        for token in response.split():
            yield token + " "