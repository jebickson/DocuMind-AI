
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_loader import load_pdf
from src.text_splitter import split_text
from src.embeddings import generate_embeddings, generate_embedding

from src.vector_store import (
    create_vector_store,
    save_vector_store,
    load_vector_store,
    search_vectors
)


def test_vector_database():

    pdf_path = PROJECT_ROOT / "data" / "sample.pdf"

    # Extract PDF
    documents = load_pdf(str(pdf_path))

    # Split text
    chunks = split_text(documents)

    # Generate embeddings
    embeddings = generate_embeddings(chunks)

    # Create FAISS index
    index = create_vector_store(chunks, embeddings)

    print("\nFAISS vectors:", index.ntotal)

    # Save database
    save_vector_store(
        index,
        chunks,
        str(PROJECT_ROOT / "vector_store")
    )

    # Load database
    loaded_index, loaded_chunks = load_vector_store(
        str(PROJECT_ROOT / "vector_store")
    )

    # Search
    question = "What is machine learning?"

    query_vector = generate_embedding(question)

    results = search_vectors(
        loaded_index,
        loaded_chunks,
        query_vector,
        top_k=3
    )

    print("\nSearch Results:")

    for result in results:
        print("\nPage:", result["page_number"])
        print("Similarity:", result["similarity_score"])
        print("Content:", result["content"])

    assert loaded_index.ntotal == len(chunks)
    assert len(results) > 0

    print("\nFAISS vector database test successful!")


if __name__ == "__main__":
    test_vector_database()
