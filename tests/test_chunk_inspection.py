
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

METADATA_PATH = PROJECT_ROOT / "vector_store" / "metadata.json"


def inspect_chunks():

    if not METADATA_PATH.exists():
        raise FileNotFoundError(
            "metadata.json not found. Process your PDF first."
        )

    with open(METADATA_PATH, "r", encoding="utf-8") as file:
        chunks = json.load(file)

    print("\n========== DOCUMIND AI CHUNK INSPECTION ==========")

    print(f"\nTotal chunks: {len(chunks)}")

    keywords = [
        "generative",
        "applications",
        "local AI",
        "advantages",
        "machine learning",
        "RAG pipeline"
    ]

    for keyword in keywords:

        print(f"\n\nSEARCH KEYWORD: {keyword}")
        print("-" * 70)

        matches = []

        for chunk in chunks:

            content = chunk.get("content", "")

            if keyword.lower() in content.lower():

                matches.append(chunk)

        if not matches:
            print("No matching chunks found.")
            continue

        for chunk in matches:

            print("\nPage:", chunk.get("page_number"))
            print("Chunk ID:", chunk.get("chunk_id"))
            print("Content:")
            print(chunk.get("content", "")[:1000])

    print("\n========== INSPECTION COMPLETED ==========")


if __name__ == "__main__":
    inspect_chunks()
