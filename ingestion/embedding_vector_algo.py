import os
import json
from sentence_transformers import SentenceTransformer
from dotenv import load_dotenv

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL")
if EMBEDDING_MODEL is None:
    raise ValueError("EMBEDDING_MODEL is not set")

def generate_embedding_vector(text: str) -> str:
    """
    Generate an embedding vector for a given text
    """
    model = SentenceTransformer(EMBEDDING_MODEL)
    embedding_vector = model.encode(text).tolist()
    return json.dumps(embedding_vector)