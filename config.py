"""
All settings live here, so you never have to hunt for "magic numbers" in the code.

Values are read from environment variables, which you normally put in a `.env`
file (copy `.env.example` to `.env` and edit it). If a variable is missing,
the default written below is used.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # reads the .env file in the project folder, if there is one

PROJECT_DIR = Path(__file__).resolve().parent

# --- Where things are stored -------------------------------------------------
DOCS_DIR = Path(os.getenv("DOCS_DIR", PROJECT_DIR / "data" / "docs"))
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", PROJECT_DIR / "data" / "chroma"))
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "company_docs")

# --- Chunking ------------------------------------------------------------------
# A chunk is a small piece of a document (~ one or two paragraphs).
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))        # max characters per chunk
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))  # characters repeated between neighbours

# --- Embeddings ----------------------------------------------------------------
# "default"      -> Chroma's built-in all-MiniLM-L6-v2 model. Small, fast, English only.
# any other name -> a sentence-transformers model from Hugging Face. For English + Arabic use
#                   "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2".
# If you change this, re-run `python ingest.py --reset`, because old vectors are not comparable.
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "default")

# --- Retrieval -----------------------------------------------------------------
TOP_K = int(os.getenv("TOP_K", "4"))  # how many chunks we give the LLM
# Cosine distance: 0 = identical meaning, 1 = unrelated. Chunks further away than this
# are thrown away. If *nothing* is close enough we answer "I don't know" without calling the LLM.
MAX_DISTANCE = float(os.getenv("MAX_DISTANCE", "0.7"))

# --- LLM -------------------------------------------------------------------------
# "ollama" (free, runs on your own computer) or "anthropic" (Claude API, needs a key).
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama")

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:3b")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-haiku-5-5")

# The exact sentence the assistant uses when the documents do not contain the answer.
I_DONT_KNOW = "I don't know. I couldn't find this in the company documents."
