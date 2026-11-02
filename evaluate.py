"""
Measure how good the assistant is, using the test questions in tests/questions.json.

The client's success rule: at least 80% of test questions answered correctly
WITH the right citation. Each test question says which file (and page/section)
holds the answer, plus a few keywords the answer must contain. Questions with
"source": null are NOT in the documents, so the correct answer is "I don't know".

    python evaluate.py                    # full test: retrieval + LLM answers
    python evaluate.py --retrieval-only   # only test the search step (no LLM needed, very fast)

Results are printed and saved to results/eval_results.csv.
"""

import argparse
import csv
import json
import time
from pathlib import Path

import config
from rag.assistant import ask
from rag.store import get_collection, search

ROOT = Path(__file__).resolve().parent


def check_retrieval(collection, q: dict) -> tuple[bool, str]:
    hits = [h for h in search(collection, q["question"], config.TOP_K) if h["distance"] <= config.MAX_DISTANCE]
    found = [f"{h['source']} ({h['location']}, {h['distance']:.2f})" for h in hits]
    if q["source"] is None:
        # Ideal: nothing passes the distance filter, so we refuse without even asking the LLM.
        # If something does pass, the LLM still gets a chance to say "I don't know".
        return not hits, "; ".join(found) or "nothing retrieved"
    ok = any(h["source"] == q["source"] and h["location"] == q["location"] for h in hits)
    return ok, "; ".join(found) or "nothing retrieved"


def check_answer(collection, q: dict) -> tuple[bool, str]:
    answer = ask(collection, q["question"])
    if q["source"] is None:
        return answer.is_unknown, answer.text
    cited_right = any(c["source"] == q["source"] for c in answer.citations)
    has_keywords = all(k.lower() in answer.text.lower() for k in q["keywords"])
    return (not answer.is_unknown) and cited_right and has_keywords, answer.text


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--retrieval-only", action="store_true", help="skip the LLM, test only the search")
    parser.add_argument("--questions", default=ROOT / "tests" / "questions.json")
    args = parser.parse_args()

    questions = json.loads(Path(args.questions).read_text(encoding="utf-8"))
    collection = get_collection()
    if collection.count() == 0:
        print("The index is empty. Run `python ingest.py` first.")
        return

    rows, passed = [], 0
    for q in questions:
        start = time.perf_counter()
        if args.retrieval_only:
            ok, detail = check_retrieval(collection, q)
        else:
            ok, detail = check_answer(collection, q)
        seconds = time.perf_counter() - start
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  #{q['id']:<3} {seconds:5.1f}s  {q['question']}")
        if not ok:
            print(f"        expected: {q['source'] or 'I dont know'} {q['location'] or ''}")
            print(f"        got:      {detail[:200]}")
        rows.append({"id": q["id"], "question": q["question"], "passed": ok,
                     "seconds": round(seconds, 2), "expected_source": q["source"], "detail": detail})

    score = 100 * passed / len(questions)
    mode = "retrieval" if args.retrieval_only else "answer"
    print(f"\n{mode} accuracy: {passed}/{len(questions)} = {score:.0f}%  (client target: 80%)")

    out = ROOT / "results" / "eval_results.csv"
    out.parent.mkdir(exist_ok=True)
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Details saved to {out}")


if __name__ == "__main__":
    main()
