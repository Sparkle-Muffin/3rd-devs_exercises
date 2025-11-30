from pathlib import Path

# Configuration constants for the RAG project

# Qdrant collection name
QDRANT_COLLECTION_NAME = "task_25"

# Vector size for embeddings
VECTOR_SIZE = 1024

# Qdrant connection settings
QDRANT_URL = "http://localhost:6333"
QDRANT_PORT = 6333

# BM25 encoding settings
BM25_ENCODINGS_DB_PATH = Path(__file__).parent.parent / "bm25_encodings_db"
