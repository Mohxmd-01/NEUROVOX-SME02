import os
from dotenv import load_dotenv

load_dotenv()

# LLM Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# Embedding Configuration
EMBEDDING_MODEL = "all-MiniLM-L6-v2"

# Paths
FAISS_INDEX_PATH = os.path.join(os.path.dirname(__file__), "faiss_index")
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "data", "documents")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "outputs")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

# Ensure directories exist
for d in [UPLOAD_DIR, OUTPUT_DIR]:
    os.makedirs(d, exist_ok=True)
