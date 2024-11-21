from mlx.nn import Linear, Embedding, LayerNorm, Module, MultiHeadAttention, GELU
import mlx.core as mx
import json
from dataclasses import dataclass
from transformers import BertTokenizer
from huggingface_hub import snapshot_download
from typing import List, Tuple, Optional
import logging
import os

@dataclass
class ModelConfig:
    """Configuration for MLX model."""
    # Match original default values
    dim: int = 1024  # Original uses dim instead of hidden_size
    num_attention_heads: int = 16
    num_hidden_layers: int = 24
    vocab_size: int = 30522
    attention_probs_dropout_prob: float = 0.1
    hidden_dropout_prob: float = 0.1
    layer_norm_eps: float = 1e-12
    max_position_embeddings: int = 512
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.dim % self.num_attention_heads != 0:
            raise ValueError(
                f"Hidden dimension ({self.dim}) must be divisible by "
                f"number of attention heads ({self.num_attention_heads})"
            )

class BertTransformerLayer(Module):
    """A transformer encoder layer with post-normalization."""
    def __init__(
        self,
        dims: int,
        num_heads: int,
        mlp_dims: Optional[int] = None,
        layer_norm_eps: float = 1e-12,
    ):
        super().__init__()
        mlp_dims = mlp_dims or dims * 4
        
        # Use MLX's built-in MultiHeadAttention
        self.attention = MultiHeadAttention(dims, num_heads, bias=True)
        self.ln1 = LayerNorm(dims, eps=layer_norm_eps)
        self.ln2 = LayerNorm(dims, eps=layer_norm_eps)
        self.linear1 = Linear(dims, mlp_dims)
        self.linear2 = Linear(mlp_dims, dims)
        self.gelu = GELU()

    def __call__(self, x, mask=None):
        # Multi-head attention with residual connection
        attention_out = self.attention(x, x, x, mask)
        add_and_norm = self.ln1(x + attention_out)

        # Feed-forward network with residual connection
        ff = self.linear1(add_and_norm)
        ff_gelu = self.gelu(ff)
        ff_out = self.linear2(ff_gelu)
        x = self.ln2(ff_out + add_and_norm)

        return x

class BertEncoder(Module):
    """BERT-style transformer encoder with multiple layers."""
    def __init__(
        self, 
        num_layers: int, 
        dims: int, 
        num_heads: int, 
        mlp_dims: Optional[int] = None
    ):
        super().__init__()
        self.layers = [
            BertTransformerLayer(dims, num_heads, mlp_dims)
            for _ in range(num_layers)
        ]

    def __call__(self, x, mask=None):
        for layer in self.layers:
            x = layer(x, mask)
        return x

class BertEmbeddings(Module):
    """BERT embeddings layer."""
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.word_embeddings = Embedding(config.vocab_size, config.dim)
        self.token_type_embeddings = Embedding(2, config.dim)
        self.position_embeddings = Embedding(
            config.max_position_embeddings, config.dim
        )
        self.norm = LayerNorm(config.dim, eps=config.layer_norm_eps)

    def __call__(self, input_ids: mx.array, token_type_ids: mx.array) -> mx.array:
        words = self.word_embeddings(input_ids)
        position = self.position_embeddings(
            mx.broadcast_to(mx.arange(input_ids.shape[1]), input_ids.shape)
        )
        token_types = self.token_type_embeddings(token_type_ids)

        embeddings = position + words + token_types
        return self.norm(embeddings)

class Bert(Module):
    """BERT model."""
    def __init__(self, config: ModelConfig):
        super().__init__()
        self.embeddings = BertEmbeddings(config)
        self.encoder = BertEncoder(
            num_layers=config.num_hidden_layers,
            dims=config.dim,
            num_heads=config.num_attention_heads,
        )
        self.pooler = Linear(config.dim, config.dim)

    def __call__(
        self,
        input_ids: mx.array,
        token_type_ids: mx.array,
        attention_mask: Optional[mx.array] = None,
    ) -> tuple[mx.array, mx.array]:
        x = self.embeddings(input_ids, token_type_ids)

        if attention_mask is not None:
            # convert 0's to -infs, 1's to 0's, and make it broadcastable
            attention_mask = mx.log(attention_mask)
            attention_mask = mx.expand_dims(attention_mask, (1, 2))

        y = self.encoder(x, attention_mask)
        return y, mx.tanh(self.pooler(y[:, 0]))

def average_pool(last_hidden_state: mx.array, attention_mask: mx.array) -> mx.array:
    """Average pool the hidden states using attention mask."""
    last_hidden = mx.multiply(last_hidden_state, attention_mask[..., None])
    return last_hidden.sum(axis=1) / attention_mask.sum(axis=1)[..., None]

class Model:
    """MLX-based embedding model wrapper."""
    def __init__(self) -> None:
        logging.info("Initializing model...")
        try:
            # Download model if not present
            model_path = snapshot_download(
                repo_id="vegaluisjose/mlx-rag",
                local_files_only=False
            )
            
            # Load config
            config_path = f"{model_path}/config.json"
            with open(config_path) as f:
                config_data = json.load(f)
                logging.info("Raw config contents:")
                for k, v in config_data.items():
                    logging.info(f"  {k}: {v}")
            
            # Create config
            self.config = ModelConfig(**config_data)
            logging.info(f"Model config: dim={self.config.dim}, "
                       f"num_heads={self.config.num_attention_heads}")
            
            # Initialize model
            self.model = Bert(self.config)
            
            # Load weights directly from file
            weights_path = f"{model_path}/model.npz"
            if not os.path.exists(weights_path):
                raise FileNotFoundError(f"Model weights not found at {weights_path}")
            
            # Load the weights directly from the file path
            self.model.load_weights(weights_path)
            
            # Initialize tokenizer
            self.tokenizer = BertTokenizer.from_pretrained("thenlper/gte-large")
            self.embedding_size = self.config.dim
            
            logging.info("Model initialization complete")
            
        except Exception as e:
            logging.error(f"Failed to initialize model: {str(e)}")
            raise

    def run(self, input_text: List[str]) -> mx.array:
        """Generate embeddings for input texts."""
        tokens = self.tokenizer(
            input_text, 
            return_tensors="np", 
            padding=True,
            truncation=True,
            max_length=self.config.max_position_embeddings
        )
        tokens = {key: mx.array(v) for key, v in tokens.items()}

        last_hidden_state, _ = self.model(**tokens)

        embeddings = average_pool(
            last_hidden_state, 
            tokens["attention_mask"].astype(mx.float32)
        )
        embeddings = embeddings / mx.linalg.norm(embeddings, ord=2, axis=1)[..., None]

        return embeddings