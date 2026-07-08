from pathlib import Path


APP_TITLE = "Local PDF AI Assistant"
APP_ICON = "📄"

DEFAULT_MODEL = "tinyllama"
FALLBACK_MODELS = [
    "tinyllama",
    "phi3",
    "gemma:2b",
    "mistral",
]

EMBEDDING_MODEL_NAME = "BAAI/bge-small-en-v1.5"
EMBEDDING_FALLBACK_MODELS = [
    "BAAI/bge-small-en-v1.5",
    "sentence-transformers/all-MiniLM-L6-v2",
]

CHUNK_SIZE = 600
CHUNK_OVERLAP = 150
RETRIEVAL_TOP_K = 8
RETRIEVAL_FETCH_K = 20
RETRIEVAL_LAMBDA_MULT = 0.7
MAX_CONTEXT_CHARS = 4200
MAX_CONTEXT_CHUNKS = 6
MEMORY_MAX_EXCHANGES = 5
LLM_TIMEOUT_SECONDS = 30
LLM_NUM_PREDICT = 72
LLM_NUM_CTX = 640
LLM_NUM_THREAD = 2

UPLOADED_PDFS_DIR = Path("uploaded_pdfs")
VECTORSTORE_DIR = Path("vectorstore")
