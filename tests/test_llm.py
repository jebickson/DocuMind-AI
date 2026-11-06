
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_store import load_vector_store
from src.retriever import retrieve_context
from src.llm import generate_answer, build_context


def test_llm_pipeline():

    print("\n" + "=" * 60)
    print("DOCUMIND AI - COMPLETE RAG PIPELINE TEST")
    print("=" * 60)

    # Step 1: Load FAISS database
    print("\nStep 1: Loading FAISS database...")

    index, chunks = load_vector_store(
        str(PROJECT_ROOT / "vector_store")
    )

    print(f"Total indexed chunks: {index.ntotal}")

    # Step 2: User question
    question = "What is machine learning?"

    print("\nStep 2: User Question:")
    print(question)

    # Step 3: Retrieve relevant PDF content
    print("\nStep 3: Retrieving relevant PDF content...")

    results = retrieve_context(
        question=question,
        index=index,
        chunks=chunks,
        top_k=5
    )

    if not results:
        print("No relevant PDF content found.")
        return

    print(f"\nRetrieved {len(results)} chunks")

    # Step 4: Display retrieval results
    print("\nStep 4: Retrieval Analysis")

    for i, result in enumerate(results, start=1):

        print(f"\n--- Retrieved Result {i} ---")

        print(
            "Similarity:",
            round(result["similarity_score"], 4)
        )

        print(
            "Chunk ID:",
            result["chunk_id"]
        )

        print(
            "Page:",
            result["page_number"]
        )

        print(
            "Source:",
            result.get("source", "Uploaded PDF")
        )

    # Step 5: Prepare complete PDF context
    print("\nStep 5: Preparing PDF context...")

    context = build_context(results)

    print("\nRetrieved Context:")
    print(context)

    # Step 6: Generate answer using Ollama
    print("\nStep 6: Generating answer with Ollama...")

    answer = generate_answer(
        question=question,
        context=context
    )

    print("\n" + "=" * 60)
    print("DOCUMIND AI ANSWER")
    print("=" * 60)

    print(answer)

    # Step 7: Validate response
    assert isinstance(answer, str)
    assert len(answer.strip()) > 0

    print("\n" + "=" * 60)
    print("COMPLETE RAG PIPELINE TEST SUCCESSFUL!")
    print("=" * 60)


if __name__ == "__main__":

    try:
        test_llm_pipeline()

    except Exception as error:

        print("\nRAG PIPELINE TEST FAILED!")
        print(type(error).__name__, ":", error)

        raise
