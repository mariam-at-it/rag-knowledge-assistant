"""
Step 2: split sections into chunks.

Why chunk at all?
  - Embedding models capture the meaning of *short* texts best. A whole 20-page
    handbook squeezed into one vector would be a blurry average of everything.
  - We can only send a limited amount of text to the LLM, so we want to send
    only the few paragraphs that matter.

How: we split on paragraphs, then glue paragraphs together until a chunk is
about CHUNK_SIZE characters. Neighbouring chunks share CHUNK_OVERLAP characters,
so a sentence that sits on a border is not cut in half and lost.
"""

import re


def _split_long_paragraph(paragraph: str, size: int) -> list[str]:
    """A single paragraph bigger than `size` is split at sentence ends."""
    sentences = re.split(r"(?<=[.!?؟])\s+", paragraph)  # ؟ is the Arabic question mark
    pieces, current = [], ""
    for sentence in sentences:
        if current and len(current) + len(sentence) + 1 > size:
            pieces.append(current)
            current = sentence
        else:
            current = f"{current} {sentence}".strip()
    if current:
        pieces.append(current)
    return pieces


def chunk_text(text: str, size: int = 800, overlap: int = 150) -> list[str]:
    paragraphs = []
    for p in re.split(r"\n\s*\n|\n", text):
        p = p.strip()
        if p:
            paragraphs.extend(_split_long_paragraph(p, size) if len(p) > size else [p])

    chunks, current = [], ""
    for p in paragraphs:
        if current and len(current) + len(p) + 1 > size:
            chunks.append(current)
            # start the next chunk with the tail of the previous one (the overlap)
            tail = current[-overlap:] if overlap else ""
            if " " in tail:
                tail = tail[tail.index(" ") + 1:]  # don't start in the middle of a word
            current = f"{tail}\n{p}".strip()
        else:
            current = f"{current}\n{p}".strip()
    if current:
        chunks.append(current)
    return chunks
