"""
Automatic tests for the pipeline. Run with:   python -m pytest -q

They do NOT need an LLM: we replace `llm.generate` with a fake function
("monkeypatching"), so we can check our own code (loading, chunking, syncing,
citation parsing, the "I don't know" path) quickly and for free.
"""

import shutil
from pathlib import Path

import pytest

import config
from rag import assistant, llm
from rag.chunking import chunk_text
from rag.loaders import load_document
from rag.store import get_collection, sync_folder

SAMPLE_DOCS = Path(__file__).resolve().parent.parent / "data" / "docs"


@pytest.fixture
def collection(tmp_path, monkeypatch):
    """A fresh index in a temporary folder, built from a copy of the sample docs."""
    docs = tmp_path / "docs"
    shutil.copytree(SAMPLE_DOCS, docs)
    monkeypatch.setattr(config, "CHROMA_DIR", tmp_path / "chroma")
    monkeypatch.setattr(config, "DOCS_DIR", docs)
    col = get_collection(reset=True)
    sync_folder(col, docs)
    return col


def test_loaders_keep_locations():
    pdf = load_document(SAMPLE_DOCS / "employee_handbook.pdf")
    assert pdf[1].location == "page 2" and "21 days" in pdf[1].text
    docx = load_document(SAMPLE_DOCS / "it_help_guide.docx")
    assert "Connecting to the VPN" in [s.location for s in docx]
    txt = load_document(SAMPLE_DOCS / "expense_policy.txt")
    assert "3. Daily Allowance" in [s.location for s in txt]


def test_chunks_respect_size_and_overlap():
    text = "\n".join(f"Sentence number {i} is here." for i in range(200))
    chunks = chunk_text(text, size=300, overlap=60)
    assert len(chunks) > 1
    assert all(len(c) <= 300 + 60 for c in chunks)
    # the start of each chunk repeats the end of the previous one
    assert chunks[1].split("\n")[0] in chunks[0]


def test_answer_with_citation(collection, monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda system, user: "You get 21 days of annual leave [1].")
    answer = assistant.ask(collection, "How many days of annual leave do I get?")
    assert not answer.is_unknown
    assert answer.citations[0]["source"] == "employee_handbook.pdf"
    assert answer.citations[0]["location"] == "page 2"


def test_unrelated_question_skips_llm(collection, monkeypatch):
    def should_not_be_called(system, user):
        raise AssertionError("the LLM must not be called when nothing relevant is found")

    monkeypatch.setattr(llm, "generate", should_not_be_called)
    answer = assistant.ask(collection, "Who won the football World Cup in 2022?")
    assert answer.is_unknown and answer.citations == []


def test_llm_says_dont_know(collection, monkeypatch):
    monkeypatch.setattr(llm, "generate", lambda system, user: config.I_DONT_KNOW)
    answer = assistant.ask(collection, "What is the dress code in the office?")
    assert answer.is_unknown and answer.citations == []


def test_update_and_delete_file(collection):
    docs = config.DOCS_DIR
    (docs / "expense_policy.txt").write_text("# Meals\nThe meal allowance is now 999 SAR.", encoding="utf-8")
    (docs / "onboarding_guide.txt").unlink()
    report = sync_folder(collection, docs)
    assert report["updated"] == ["expense_policy.txt"]
    assert report["removed"] == ["onboarding_guide.txt"]
    sources = {m["source"] for m in collection.get(include=["metadatas"])["metadatas"]}
    assert "onboarding_guide.txt" not in sources
    texts = collection.get(where={"source": "expense_policy.txt"})["documents"]
    assert texts == ["Meals\nThe meal allowance is now 999 SAR."]
