
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.vector_store import load_vector_store
from src.retriever import retrieve_context


def test_rag_evaluation():

    index, chunks = load_vector_store(
        str(PROJECT_ROOT / "vector_store")
    )

    test_questions = [
        "What are the five applications of Generative AI?",
        "What is Machine Learning?",
        "What is the difference between Machine Learning and Deep Learning?",
        "What are the six stages of a RAG pipeline?",
        "What are the advantages of local AI model execution?"
    ]

    print("\n========== DOCUMIND AI RAG EVALUATION ==========\n")

    for number, question in enumerate(test_questions, 1):

        print(f"\nQUESTION {number}: {question}")
        print("-" * 70)

        results = retrieve_context(
            question=question,
            index=index,
            chunks=chunks,
            top_k=5
        )

        if not results:
            print("No results retrieved.")
            continue

        for rank, result in enumerate(results, 1):

            print(f"\nResult {rank}")
            print("Page:", result["page_number"])
            print("Chunk ID:", result["chunk_id"])
            print("Similarity:", round(result["similarity_score"], 4))
            print("Keyword overlap:", round(result["keyword_overlap"], 4))
            print("Combined score:", round(result["combined_score"], 4))
            print("Content:", result["content"][:500])

    print("\n========== EVALUATION COMPLETED ==========")


if __name__ == "__main__":
    test_rag_evaluation()
