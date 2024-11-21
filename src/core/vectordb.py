import duckdb
from typing import List, Dict, Any, Optional, Union
import logging
from .model import Model
import numpy as np
from dataclasses import dataclass
import os
import uuid
from .pdf_utils import process_pdf
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO)

@dataclass
class VectorDB:
    """Vector database for document storage and retrieval."""
    db_path: str
    model: Optional[Model] = None
    use_persistent: bool = True
    conn: Optional[Any] = None
    verbose: bool = False
    
    def __post_init__(self):
        """Initialize database connection and model."""
        if not self.model:
            self.model = Model()
            
        if self.use_persistent:
            # Connect to existing database or create new one
            self.conn = duckdb.connect(self.db_path)
        else:
            self.conn = duckdb.connect(':memory:')
            
        # Load VSS extension
        self.conn.execute("INSTALL vss")
        self.conn.execute("LOAD vss")
        
        # Initialize tables if they don't exist
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS documents (
                id VARCHAR PRIMARY KEY,
                content VARCHAR,
                source VARCHAR,
                embedding_type VARCHAR,
                prompt VARCHAR
            )
        """)
        
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                document_id VARCHAR PRIMARY KEY,
                embedding DOUBLE[]
            )
        """)
        
        # Force write to disk
        self.conn.execute("CHECKPOINT")
            
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None

    def ingest(self, content: str, source: str, summary_type: str = "finding", prompt: str = "") -> None:
        """Add document to database with embedding."""
        try:
            # Generate document ID
            doc_id = str(uuid.uuid4())
            
            # Add document
            self.conn.execute("""
                INSERT INTO documents (id, content, source, embedding_type, prompt)
                VALUES (?, ?, ?, ?, ?)
            """, [doc_id, content, source, summary_type, prompt])
            
            # Generate and add embedding
            embedding = self.model.run([content])[0].tolist()  # Convert to Python list
            
            self.conn.execute("""
                INSERT INTO embeddings (document_id, embedding)
                VALUES (?, ?)
            """, [doc_id, embedding])
            
            # Commit changes
            self.conn.commit()
            
        except Exception as e:
            logging.error(f"Failed to ingest document: {str(e)}")
            raise
            
    def search(
        self, 
        query: str, 
        top_k: int = 3,
        summary_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.
        
        Args:
            query: Search query
            top_k: Number of results to return
            summary_type: Optional filter by summary type ('concepts', 'technical', 'context')
        """
        try:
            # Get query embedding
            query_embedding = self.model.run([query])[0]
            
            # Build search query with optional summary type filter
            sql = """
                WITH distances AS (
                    SELECT 
                        d.id,
                        d.content,
                        d.source,
                        d.embedding_type,
                        array_cosine_distance(e.embedding::FLOAT[1024], ?::FLOAT[1024]) as distance
                    FROM documents d
                    JOIN embeddings e ON d.id = e.document_id
                    WHERE 1=1
            """
            
            params = [query_embedding.tolist()]
            
            # Add summary type filter if specified
            if summary_type:
                sql += " AND d.embedding_type = ?"
                params.append(summary_type)
                
            sql += """
                    ORDER BY distance ASC
                    LIMIT ?
                )
                SELECT 
                    id,
                    content,
                    source,
                    embedding_type,
                    (1.0 - distance) as similarity
                FROM distances
            """
            params.append(top_k)
            
            # Execute search
            results = self.conn.execute(sql, params).fetchall()
            
            # Format results
            return [{
                'id': str(r[0]),
                'content': r[1],
                'source': r[2],
                'embedding_type': r[3],
                'similarity': float(r[4])
            } for r in results]
            
        except Exception as e:
            logging.error(f"Search failed: {str(e)}")
            return []

    def get_document_count(self) -> int:
        """Get total number of documents."""
        return self.conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0]

    def get_embedding_count(self) -> int:
        """Get total number of embeddings."""
        return self.conn.execute("SELECT COUNT(*) FROM embeddings").fetchone()[0]

    def ingest_pdf(self, pdf_path: str) -> None:
        """Ingest a PDF file into the database."""
        try:
            # Process PDF into chunks
            for chunk in process_pdf(pdf_path):
                if chunk.strip():  # Only ingest non-empty chunks
                    self.ingest(
                        content=chunk,
                        source=pdf_path
                    )
                    
        except Exception as e:
            logging.error(f"Failed to ingest PDF {pdf_path}: {str(e)}")
            raise
    def ingest_gemini_summaries(self, jsonl_dir: Union[str, Path]) -> None:
        """Ingest all Gemini-processed summaries from a directory."""
        jsonl_dir = Path(jsonl_dir)
        
        # Process each JSONL file
        for jsonl_path in jsonl_dir.glob('*_gemini.jsonl'):
            try:
                with open(jsonl_path) as f:
                    for line in f:
                        data = json.loads(line)
                        
                        # Extract content, source, and metadata
                        content = data['content']
                        source = data['metadata']['source_file']
                        prompt = data['metadata']['prompt']
                        summary_type = data['metadata']['summary_type']  # Now directly from metadata
                        
                        # Add to database with metadata
                        self.ingest(
                            content=content,
                            source=source,
                            summary_type=summary_type,
                            prompt=prompt
                        )
                        
                logging.info(f"Ingested summaries from {jsonl_path.name}")
                
            except Exception as e:
                logging.error(f"Failed to process {jsonl_path}: {str(e)}")
