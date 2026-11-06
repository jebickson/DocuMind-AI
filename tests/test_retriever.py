
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_store import load_vector_store
from src.retriever import retrieve_context, format_context


def test_retrieval():

    # Load saved FAISS database
    index, chunks = load_vector_store(
        str(PROJECT_ROOT / "vector_store")
    )

    # Ask a question
    question = "What is machine learning?"

    print("\nUser Question:", question)

    # Retrieve relevant passages
    results = retrieve_context(
        question=question,
        index=index,
        chunks=chunks,
        top_k=3
    )

    # Display results
    print("\nRetrieved Results:")

    for result in results:

        print("\nPage:", result["page_number"])
        print("Similarity:", result["similarity_score"])
        print("Content:", result["content"])

    # Format context for LLM
    context = format_context(results)

    print("\nFormatted Context:")
    print(context)

    assert len(results) > 0
    assert "PDF Page" in context

    print("\nSemantic retrieval test successful!")


if __name__ == "__main__":
    test_retrieval()
