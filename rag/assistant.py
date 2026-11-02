"""
Step 5: answer a question = Retrieve + Augment + Generate (that's what RAG means).

  1. Retrieve: find the chunks closest in meaning to the question.
  2. Filter:   drop chunks that are too far away (MAX_DISTANCE). If nothing is
               left, say "I don't know" right away. No LLM call, no made-up answer.
  3. Augment:  put the remaining chunks into the prompt, numbered [1], [2], ...
  4. Generate: the LLM answers ONLY from those chunks and cites the numbers.
  5. Cite:     we read which [n] the LLM used and turn them into file + location.

There are two safety nets against made-up answers ("hallucinations"):
  - the distance filter in step 2, and
  - the instruction in the prompt to reply with I_DONT_KNOW when the chunks
    don't contain the answer.
"""

import re
from dataclasses import dataclass, field

import config
from rag import llm
from rag.store import search

SYSTEM_PROMPT = f"""You are the internal knowledge assistant of a company.
Answer employee questions using ONLY the numbered document excerpts you are given.

Rules:
- After every fact, cite the excerpt it came from in square brackets, like [1] or [2][3].
- If the excerpts do not contain the answer, reply with exactly: {config.I_DONT_KNOW}
- Never use outside knowledge and never guess.
- Be short and clear. Answer in the same language as the question."""


@dataclass
class Answer:
    text: str
    citations: list[dict] = field(default_factory=list)  # [{"source": ..., "location": ...}]
    retrieved: list[dict] = field(default_factory=list)  # every chunk we looked at (for debugging)

    @property
    def is_unknown(self) -> bool:
        return self.text.strip().startswith("I don't know")


def build_prompt(question: str, chunks: list[dict]) -> str:
    excerpts = "\n\n".join(
        f"[{i}] (from {c['source']}, {c['location']})\n{c['text']}" for i, c in enumerate(chunks, start=1)
    )
    return f"Document excerpts:\n\n{excerpts}\n\nQuestion: {question}"


def ask(collection, question: str) -> Answer:
    retrieved = search(collection, question, config.TOP_K)
    relevant = [c for c in retrieved if c["distance"] <= config.MAX_DISTANCE]
    if not relevant:
        return Answer(config.I_DONT_KNOW, [], retrieved)

    text = llm.generate(SYSTEM_PROMPT, build_prompt(question, relevant))
    if config.I_DONT_KNOW.split(".")[0].lower() in text.lower():
        return Answer(config.I_DONT_KNOW, [], retrieved)

    # Turn "[2]" markers into real sources. A source cited twice is listed once.
    citations, seen = [], set()
    for number in re.findall(r"\[(\d+)\]", text):
        index = int(number) - 1
        if 0 <= index < len(relevant):
            key = (relevant[index]["source"], relevant[index]["location"])
            if key not in seen:
                seen.add(key)
                citations.append({"number": int(number), "source": key[0], "location": key[1]})
    return Answer(text, citations, retrieved)
