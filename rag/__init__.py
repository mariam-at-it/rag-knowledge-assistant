"""The core RAG (Retrieval-Augmented Generation) building blocks.

Read the modules in this order, it follows the path of a document:
  loaders.py   -> read PDF / DOCX / TXT files into text sections
  chunking.py  -> cut sections into small overlapping chunks
  store.py     -> turn chunks into vectors (embeddings) and save them in Chroma
  llm.py       -> talk to the language model (Ollama or Claude)
  assistant.py -> retrieve chunks for a question and ask the LLM for a cited answer
"""
