"""
Index the documents folder into Chroma.

    python ingest.py            # add new files, re-index changed ones, remove deleted ones
    python ingest.py --reset    # throw the whole index away and rebuild it from scratch

Run it again any time you add, edit or delete a file in data/docs/.
"""

import argparse

import config
from rag.store import get_collection, sync_folder


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--reset", action="store_true", help="delete the index and rebuild it")
    args = parser.parse_args()

    collection = get_collection(reset=args.reset)
    report = sync_folder(collection, config.DOCS_DIR)

    for status, files in report.items():
        for name in files:
            print(f"  {status:<9} {name}")
    print(f"\nIndex now holds {collection.count()} chunks from {config.DOCS_DIR}")


if __name__ == "__main__":
    main()
