# RAG Knowledge Assistant: Step 1 prototype

An internal assistant that answers employee questions from company documents
(HR handbooks, IT guides, policies), **cites the exact document and section**,
and says **"I don't know"** when the documents don't contain the answer.

This is the first step of the graduation project: the core loop in plain
Python, with no web UI, login or database yet. Everything else (FastAPI, React,
roles, feedback) will be built around this loop later.

```
upload docs  ->  ask a question  ->  get an answer with citations
```

---

## 1. What is RAG? (the idea in 1 minute)

A language model (LLM) like Claude or Llama knows a lot about the world but
nothing about *your* company. RAG (**R**etrieval-**A**ugmented **G**eneration)
fixes that without retraining the model:

1. **Retrieve**: find the few paragraphs in your documents that are most
   related to the question.
2. **Augment**: paste those paragraphs into the prompt.
3. **Generate**: ask the LLM to answer *only* from those paragraphs, and to
   say which paragraph each fact came from.

```
                       INDEXING (once, and when files change)
  data/docs/*.pdf|docx|txt
          │  loaders.py      read text, remember page / section
          ▼
      sections
          │  chunking.py     cut into ~800-character overlapping chunks
          ▼
       chunks
          │  store.py        embedding model turns each chunk into a vector
          ▼
   Chroma vector DB  (data/chroma/)

                       ANSWERING (every question)
  "How many vacation days do I get?"
          │  store.search    embed the question, find the 4 closest chunks
          ▼
  closest chunks ── none close enough? ──► "I don't know"  (no LLM call)
          │  assistant.py    build prompt with chunks numbered [1] [2] ...
          ▼
        LLM  (llm.py: Ollama on your PC, or Claude API)
          │
          ▼
  "You get 21 days per year [1]."   +   [1] employee_handbook.pdf, page 2
```

### Key words

| Word | Meaning |
|---|---|
| **Chunk** | A small piece of a document, about 1–2 paragraphs. We search chunks, not whole files. |
| **Embedding** | A list of numbers that represents the *meaning* of a text. "vacation days" and "annual leave" get similar numbers even though the words differ. |
| **Vector database** | A database that stores embeddings and can quickly find the ones closest to a question. We use **Chroma**, which runs inside Python and saves to a folder. |
| **Cosine distance** | How far apart two meanings are: 0 = same meaning, 1 = unrelated. |
| **Hallucination** | When an LLM confidently invents an answer. The distance filter and the strict prompt are our two defences. |

---

## 2. Setup

You need **Python 3.11 or newer** and **Git**.

### 2.1 Get the code

```bash
git clone https://github.com/<your-username>/rag-knowledge-assistant.git
cd rag-knowledge-assistant
```

### 2.2 Create a virtual environment and install packages

A *virtual environment* is a private folder of Python packages for this
project, so it doesn't clash with other projects on your computer.

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS / Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

You'll see `(.venv)` at the start of your terminal line when it's active. Run
the activate command again every time you open a new terminal.

### 2.3 Choose your LLM

Copy the settings file: `cp .env.example .env` (on Windows: `copy .env.example .env`).

**Option A: Ollama (free, runs on your laptop, default)**
1. Install Ollama from <https://ollama.com/download>.
2. Download a model: `ollama pull qwen2.5:3b` (about 2 GB; Qwen handles Arabic well).
3. Leave `LLM_PROVIDER=ollama` in `.env`.

This matches the client's "data stays private / self-hosted" requirement:
nothing leaves your machine. With 8 GB of RAM or less, try `qwen2.5:1.5b`.

**Option B: Claude API (better answers, small cost)**
1. Create a key at <https://console.anthropic.com>.
2. In `.env` set `LLM_PROVIDER=anthropic` and `ANTHROPIC_API_KEY=sk-ant-...`.

`.env` is listed in `.gitignore`, so your key is never uploaded to GitHub.

---

## 3. Run it

```bash
# (optional) recreate the sample documents
python scripts/make_sample_docs.py

# 1. index the documents in data/docs/
python ingest.py

# 2. ask a question
python ask.py "How many days of annual leave do I get?"
python ask.py --show-chunks "My VPN won't connect"   # also see what was retrieved
python ask.py                                       # interactive mode

# 3. measure quality on the 20 test questions
python evaluate.py --retrieval-only   # search step only, no LLM needed
python evaluate.py                    # full answers (needs Ollama or Claude)

# 4. automatic tests of the code (no LLM needed)
python -m pytest -q
```

Example output (the exact wording depends on the LLM):

```
You get 21 days of paid annual leave per year, rising to 25 days after five years of service [1].

Sources:
  [1] employee_handbook.pdf, page 2
```

### Using your own documents

Put PDF, DOCX or TXT files into `data/docs/` and run `python ingest.py` again.
It adds new files, **re-indexes files that changed**, and **removes files you
deleted**, so answers always match the folder. It knows a file changed by
comparing its SHA-256 fingerprint (hash).

---

## 4. Tour of the code

Read the files in this order, it follows the journey of a document:

| File | What it does |
|---|---|
| `config.py` | Every setting in one place, read from `.env`. |
| `rag/loaders.py` | Reads PDF (one section per **page**), DOCX (one section per **heading**) and TXT (one section per `# heading`). Keeping the location is what makes precise citations possible. |
| `rag/chunking.py` | Splits sections into ~800-character chunks along paragraph and sentence borders, with 150 characters of overlap so nothing is cut in half. |
| `rag/store.py` | Creates the Chroma collection, embeds and stores chunks with their metadata, keeps the index in sync with the folder, and searches. |
| `rag/llm.py` | One `generate(system, user)` function that talks to Ollama or Claude. |
| `rag/assistant.py` | The RAG logic: search, distance filter, prompt, LLM call, and turning `[1]` markers into real citations. |
| `ingest.py`, `ask.py`, `evaluate.py` | Small command-line programs that use the pieces above. |
| `scripts/make_sample_docs.py` | Builds the made-up "Nimbus Systems" documents. |
| `tests/questions.json` | 20 test questions: 16 answerable (with the expected file, page/section and keywords) and 4 that are **not** in the documents. |
| `tests/test_pipeline.py` | Automatic tests with a fake LLM. |

### How "I don't know" works

There are two safety nets:

1. **Before the LLM**: if no chunk is closer than `MAX_DISTANCE` (0.7), we
   answer "I don't know" immediately. For example, "Who won the World Cup?"
   has a best distance of 0.90.
2. **Inside the LLM**: the system prompt says to reply with the exact
   "I don't know" sentence when the excerpts don't contain the answer. This
   catches questions that *sound* related but aren't answered, such as "What
   is the dress code?" (distance 0.74: close to the onboarding guide, but the
   guide says nothing about clothes).

### How the evaluation decides "correct"

- **Answerable question**: the answer is not "I don't know", it contains all
  the expected keywords (e.g. "21"), and it cites the expected file.
- **Unanswerable question**: the answer is "I don't know".

The client's success target is **80% correct with the right citation**.

---

## 5. Current results

Measured with the default English embedding model (`all-MiniLM-L6-v2`):

| Check | Result |
|---|---|
| Automatic tests (`pytest`) | 6 / 6 pass |
| Search finds the right file **and** page/section (16 answerable questions) | 16 / 16 |
| Unrelated questions stopped before the LLM (4 questions) | 2 / 4 (the other 2 go to the LLM's "I don't know" rule) |
| Search time per question | about 0.2 s |
| Full answer accuracy (`python evaluate.py`) | *not measured yet: run it with your chosen LLM and record the number here* |

The distances of correct chunks were 0.24–0.67 and those of unanswerable
questions 0.74–0.90, which is why `MAX_DISTANCE` is 0.7. With only 20
questions this is a rough setting, so re-check it when you add real documents.

---

## 6. Arabic support

The default embedding model only understands English. For English **and**
Arabic questions:

```bash
pip install sentence-transformers
# in .env:
EMBEDDING_MODEL=sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2
python ingest.py --reset   # vectors from different models can't be mixed
```

With a multilingual model, an Arabic question can find an English paragraph
and the other way round. The prompt already tells the LLM to answer in the
language of the question. Distances are different with a new model, so run
`python evaluate.py --retrieval-only` and adjust `MAX_DISTANCE`.

---

## 7. Working with Git and GitHub

GitHub stores this project online with the full history of every change.

```bash
git pull                     # download the latest changes from GitHub
git status                   # see which files you changed
git add .                    # mark all changes to be saved
git commit -m "Describe what you changed"   # save a snapshot locally
git push                     # upload your snapshots to GitHub
```

A good habit: commit after every small working step, with a message that says
*what* and *why*.

---

## 8. Next steps (from the project roadmap)

- Run `python evaluate.py` with a real LLM and record the score above.
- Add Arabic test questions and try the multilingual embedding model.
- Week 3: write the SRS document.
- Week 4–6: wrap `rag.assistant.ask` in a FastAPI backend, with PostgreSQL for users and chat history.
- Week 9–10: role-based access. Store a `roles` field in each chunk's metadata
  (e.g. `salary_policy.docx` -> `hr`) and pass a `where` filter to Chroma's
  `query` so users only retrieve chunks they are allowed to see.
