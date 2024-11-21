from dataclasses import dataclass, field
from typing import List, Dict, Generator, Optional, Union, Tuple
import logging
from .chat import Chat
from ..core.vectordb import VectorDB
from mlx_lm.utils import load, generate
import json
import os
import mlx.core as mx


logging.basicConfig(level=logging.INFO)

SYSTEM_PROMPT = """
You are Dr. Sedman, an expert in sedimentology and geomorphology. Your purpose is to synthesize information from provided sources into clear and concise responses.

RULES:
1. ONLY use information between [CONTEXT START] and [CONTEXT END].
2. Format your response as a SINGLE well-developed paragraph that:
   - Fully explains the concept
   - Connects related ideas
   - Provides sufficient detail
   - Uses proper scientific language
3. Include relevant citations using [Author, Year] format.
4. After completing your paragraph, add <STOP> to indicate completion.
5. If information isn't in sources, say "Based on the available sources, I cannot provide information about [topic]" and <STOP>.
6. <STOP> marks the absolute end - no text after this will be processed.

7. DO NOT:
   - Generate new questions
   - Add commentary
   - Offer to answer more
   - Continue past your paragraph
   - Process any new context after answering
   - Add any text after <STOP>
   - Use periods or other punctuation after <STOP>

Example:
[CONTEXT START]
----------------------------------------
{"statement": "The Volga delta has flat gradients", "source": "Smith_2020.pdf"}
{"statement": "The flat gradients affect sediment transport", "source": "Jones_2021.pdf"}
----------------------------------------
[CONTEXT END]

Question: What is unique about the Volga delta?
Answer: The Volga delta is characterized by its distinctively flat gradients [Smith, 2020], which play a crucial role in controlling how sediment is transported and deposited throughout the delta system [Jones, 2021]. <STOP>
"""

@dataclass
class SamplerConfig:
    """Configuration for response sampling."""
    # Entropy thresholds
    low_entropy: float = 2.0
    high_entropy: float = 4.0
    low_varentropy: float = 0.5
    high_varentropy: float = 2.0
    
    # Response templates
    clarifying_template: str = "Could you please clarify what you mean about {}? <STOP>"
    uncertain_template: str = "Based on the available sources, I cannot provide a definitive answer about {}. <STOP>"
    cautious_template: str = "{} (Note: This interpretation is based on limited evidence) <STOP>"

@dataclass
class Bot:
    """Dr. Sedman bot."""
    name: str = "Dr. Sedman"
    role: str = "Sedimentologist"
    model_name: str = "meta-llama/Llama-3.2-3B-Instruct"
    db: Optional[VectorDB] = None
    chat: Optional[Chat] = None
    min_similarity: float = 0.6
    sampler_config: SamplerConfig = field(default_factory=SamplerConfig)
    
    def __post_init__(self):
        """Initialize model."""
        self.model, self.tokenizer = load(self.model_name)

    def calculate_entropy(self, logits: mx.array) -> Tuple[float, float]:
        """Calculate entropy and varentropy of response logits."""
        # Skip entropy calculation for non-array inputs
        if not isinstance(logits, mx.array):
            return 0.0, 0.0
        
        # Calculate entropy using available MLX functions
        probs = mx.softmax(logits, axis=-1)  # Use softmax directly
        log_probs = mx.log(mx.clip(probs, 1e-10, 1.0))  # Add clip for numerical stability
        
        # Calculate entropy in bits
        entropy = -mx.sum(probs * log_probs) / mx.array(2.0).log()
        
        # Calculate varentropy
        mean_entropy = mx.mean(entropy)
        varentropy = mx.mean((entropy - mean_entropy) ** 2)
        
        return float(entropy), float(varentropy)
        
    def get_response(self, query: str) -> Union[str, Generator[str, None, None]]:
        """Generate response with entropy-based sampling."""
        try:
            # Get relevant chunks from database
            context = None
            if self.db:
                print("\nFinding relevant sources...")
                
                # Get all results
                results = self.db.search(query, top_k=4)
                
                if results:
                    # Sort by similarity and filter
                    results.sort(key=lambda x: x['similarity'], reverse=True)
                    relevant = [r for r in results if r['similarity'] >= self.min_similarity]
                    
                    if relevant:
                        # Group by type
                        findings = []
                        methods = []
                        relationships = []
                        
                        # Show matching sources by type
                        print("\nRelevant sources:")
                        for r in relevant:
                            source = os.path.basename(r['source']).replace('_gemini.jsonl', '')
                            print(f"- {source} ({r['embedding_type']}, similarity: {r['similarity']:.2f})")
                            
                            try:
                                content = json.loads(r['content'])
                                content['source'] = source
                                
                                if r['embedding_type'] == 'finding':
                                    findings.append(content)
                                elif r['embedding_type'] == 'methodology':
                                    methods.append(content)
                                elif r['embedding_type'] == 'relationship':
                                    relationships.append(content)
                                    
                            except json.JSONDecodeError:
                                logging.warning(f"Invalid JSON content: {r['content'][:100]}...")
                                continue
                        
                        print()
                        
                        # Format context with organized sections
                        context = "[CONTEXT START]\n"
                        context += "="*80 + "\n"
                        
                        if findings:
                            context += "FINDINGS:\n" + "-"*80 + "\n"
                            for f in findings:
                                context += json.dumps(f, ensure_ascii=False) + "\n"
                            context += "-"*80 + "\n\n"
                            
                        if relationships:
                            context += "RELATIONSHIPS:\n" + "-"*80 + "\n"
                            for r in relationships:
                                context += json.dumps(r, ensure_ascii=False) + "\n"
                            context += "-"*80 + "\n\n"
                            
                        if methods:
                            context += "METHODOLOGY:\n" + "-"*80 + "\n"
                            for m in methods:
                                context += json.dumps(m, ensure_ascii=False) + "\n"
                            context += "-"*80 + "\n"
                        
                        context += "="*80 + "\n"
                        context += "[CONTEXT END]\n"

            # Build prompt with clearer structure
            prompt = (
                f"{SYSTEM_PROMPT}\n\n"
                f"CURRENT QUERY: {query}\n"
                f"AVAILABLE INFORMATION:\n"
                f"{context if context else 'No specific sources available for this query.'}\n"
                f"DR. SEDMAN'S RESPONSE: "
            )

            # Generate base response
            response = generate(
                self.model,
                self.tokenizer,
                prompt=prompt,
                max_tokens=256,
                temp=0.0,
                verbose=False
            )
            
            # Add <STOP> token for all responses
            if not context:
                return "Based on the available sources, I cannot provide information about this topic. <STOP>"
            
            return str(response) + " <STOP>"
                
        except Exception as e:
            logging.error(f"Error generating response: {str(e)}")
            return f"I apologize, I encountered an error: {str(e)} <STOP>"