"""
Step 3: embeddings + the vector database (Chroma).

An *embedding* is a list of numbers (a vector) that represents the meaning of a
text. Texts with similar meaning get vectors that point in similar directions,
even if they use different words ("vacation days" vs "annual leave").

Chroma stores each chunk together with:
  - its vector    -> used to find chunks similar to the question
  - its text      -> what we later show to the LLM
  - its metadata  -> source file, location (page/section), file hash
Chroma computes the vectors for us using the embedding function we give it.

Keeping the index in sync with the folder (client requirement: "updating or
deleting a file updates the answers"): we store a hash (fingerprint) of each
file. On every ingest we compare hashes and only re-index files that changed,
and remove chunks of files that were deleted.
"""

import hashlib
from pathlib import Path

import chromadb
from chromadb.utils import embedding_functions

import config
from rag.chunking import chunk_text
from rag.loaders import SUPPORTED_EXTENSIONS, load_document


def get_embedding_function():
    if config.EMBEDDING_MODEL == "default":
        return embedding_functions.DefaultEmbeddingFunction()
    # Needs `pip install sentence-transformers` (downloads the model the first time).
    return embedding_functions.SentenceTransformerEmbeddingFunction(model_name=config.EMBEDDING_MODEL)


def get_collection(reset: bool = False):
    client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))  # saved on disk
    if reset:
        try:
            client.delete_collection(config.COLLECTION_NAME)
        except Exception:
            pass  # it did not exist yet
    return client.get_or_create_collection(
        name=config.COLLECTION_NAME,
        embedding_function=get_embedding_function(),
        metadata={"hnsw:space": "cosine"},  # compare vectors by angle (cosine distance)
    )


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def index_file(collection, path: Path) -> int:
    """Load, chunk and store one file. Returns the number of chunks added."""
    remove_file(collection, path.name)  # drop old chunks of this file first
    digest = file_hash(path)
    ids, texts, metadatas = [], [], []
    for section in load_document(path):
        for chunk in chunk_text(section.text, config.CHUNK_SIZE, config.CHUNK_OVERLAP):
            ids.append(f"{path.name}::{len(ids)}")  # unique id, e.g. "it_help_guide.docx::3"
            texts.append(chunk)
            metadatas.append({"source": path.name, "location": section.location, "file_hash": digest})
    if ids:
        collection.add(ids=ids, documents=texts, metadatas=metadatas)
    return len(ids)


def remove_file(collection, file_name: str) -> None:
    collection.delete(where={"source": file_name})


def indexed_files(collection) -> dict[str, str]:
    """{file name: hash} for every file currently in the index."""
    records = collection.get(include=["metadatas"])
    return {m["source"]: m["file_hash"] for m in records["metadatas"]}


def sync_folder(collection, folder: Path) -> dict[str, list[str]]:
    """Make the index match the folder: add new files, re-index changed ones, delete removed ones."""
    report = {"added": [], "updated": [], "unchanged": [], "removed": []}
    on_disk = {p.name: p for p in sorted(folder.iterdir()) if p.suffix.lower() in SUPPORTED_EXTENSIONS}
    in_index = indexed_files(collection)

    for name, path in on_disk.items():
        if name not in in_index:
            index_file(collection, path)
            report["added"].append(name)
        elif in_index[name] != file_hash(path):
            index_file(collection, path)
            report["updated"].append(name)
        else:
            report["unchanged"].append(name)

    for name in in_index:
        if name not in on_disk:
            remove_file(collection, name)
            report["removed"].append(name)
    return report


def search(collection, question: str, top_k: int) -> list[dict]:
    """Return the top_k chunks closest in meaning to the question, best first."""
    if collection.count() == 0:
        return []
    result = collection.query(query_texts=[question], n_results=min(top_k, collection.count()))
    hits = []
    for text, meta, distance in zip(result["documents"][0], result["metadatas"][0], result["distances"][0]):
        hits.append({"text": text, "source": meta["source"], "location": meta["location"], "distance": distance})
    return hits
