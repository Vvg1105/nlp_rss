import os
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

# Use environment variable or default to a good general-purpose model
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Cache the model (load once, reuse many times)
_model = None

def get_model():
    """
    Get or load the sentence transformer model (singleton pattern)
    """
    global _model
    if _model is None:
        print(f"Loading embedding model: {EMBEDDING_MODEL}...")
        _model = SentenceTransformer(EMBEDDING_MODEL)
        print("Model loaded successfully!")
    return _model

def generate_embedding_vector(text: str) -> str:
    """
    Generate an embedding vector for a given text
    
    Args:
        text: Input text to embed
        
    Returns:
        JSON string of embedding vector
    """
    model = get_model()  # Reuse loaded model
    embedding_vector = model.encode(text).tolist()
    return json.dumps(embedding_vector)