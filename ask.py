"""
Ask the assistant questions from the terminal.

    python ask.py "How many days of annual leave do I get?"
    python ask.py                      # interactive mode, type 'exit' to quit
    python ask.py --show-chunks "..."  # also print the chunks that were retrieved
"""

import argparse
import time

from rag.assistant import ask
from rag.store import get_collection


def print_answer(answer, elapsed: float, show_chunks: bool) -> None:
    print(f"\n{answer.text}\n")
    if answer.citations:
        print("Sources:")
        for c in answer.citations:
            print(f"  [{c['number']}] {c['source']}, {c['location']}")
    if show_chunks:
        print("\nRetrieved chunks (smaller distance = more similar):")
        for c in answer.retrieved:
            preview = c["text"][:90].replace("\n", " ")
            print(f"  {c['distance']:.3f}  {c['source']}, {c['location']}: {preview}...")
    print(f"\n({elapsed:.1f}s)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("question", nargs="?", help="the question; leave out for interactive mode")
    parser.add_argument("--show-chunks", action="store_true", help="print the retrieved chunks too")
    args = parser.parse_args()

    collection = get_collection()
    if collection.count() == 0:
        print("The index is empty. Run `python ingest.py` first.")
        return

    questions = [args.question] if args.question else None
    while True:
        question = questions.pop() if questions else input("\nAsk a question (or 'exit'): ").strip()
        if not question or question.lower() in ("exit", "quit"):
            break
        start = time.perf_counter()
        answer = ask(collection, question)
        print_answer(answer, time.perf_counter() - start, args.show_chunks)
        if args.question:
            break


if __name__ == "__main__":
    main()
