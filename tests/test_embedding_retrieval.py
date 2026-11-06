
import sys
from pathlib import Path

# =====================================================
# 1. PROJECT PATH
# =====================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

sys.path.insert(0, str(PROJECT_ROOT))


# =====================================================
# 2. IMPORT MODULES
# =====================================================

from src.pdf_loader import load_pdf
from src.text_splitter import split_text

from src.embeddings import (
    generate_embeddings,
    generate_embedding
)

from src.vector_store import (
    create_vector_store,
    search_vectors
)


# =====================================================
# 3. TEST CONFIGURATION
# =====================================================

PDF_PATH = (
    PROJECT_ROOT
    / "data"
    / "DocuMind_AI_Test_Document.pdf"
)

QUESTIONS = [
    "What is Artificial Intelligence?",
    "What is Machine Learning?",
    "What is FAISS used for?",
    "What is Python used for in AI?",
    "What are the six stages of a RAG pipeline?"
]

TOP_K = 5


# =====================================================
# 4. MAIN RETRIEVAL TEST
# =====================================================

def test_embedding_retrieval():

    print("\n" + "=" * 60)
    print("DOCUMIND AI - EMBEDDING RETRIEVAL TEST")
    print("=" * 60)

    # Step 1: Check PDF

    if not PDF_PATH.exists():

        raise FileNotFoundError(
            f"PDF not found: {PDF_PATH}"
        )

    print("\n[1] Loading PDF...")

    documents = load_pdf(str(PDF_PATH))

    if not documents:

        raise ValueError(
            "No text extracted from PDF."
        )

    print("PDF loaded successfully!")
    print("Total pages:", len(documents))


    # Step 2: Split PDF into chunks

    print("\n[2] Splitting PDF into chunks...")

    chunks = split_text(documents)

    if not chunks:

        raise ValueError(
            "No chunks generated."
        )

    print("Total chunks:", len(chunks))


    # Step 3: Generate document embeddings

    print("\n[3] Generating document embeddings...")

    vectors = generate_embeddings(chunks)

    print("Embeddings generated successfully!")
    print("Embedding shape:", vectors.shape)


    # Step 4: Create FAISS index

    print("\n[4] Creating FAISS index...")

    index = create_vector_store(
        chunks,
        vectors
    )

    print("FAISS index created successfully!")
    print("Total vectors:", index.ntotal)


    # Step 5: Test retrieval questions

    print("\n[5] Testing semantic retrieval...")

    for question_number, question in enumerate(
        QUESTIONS,
        start=1
    ):

        print("\n" + "=" * 60)

        print(
            f"QUESTION {question_number}: {question}"
        )

        print("=" * 60)


        # Generate query embedding

        query_vector = generate_embedding(
            question
        )


        # Search FAISS database

        results = search_vectors(
            index=index,
            chunks=chunks,
            query_embedding=query_vector,
            top_k=TOP_K
        )


        if not results:

            print("No results found.")

            continue


        # Display retrieved chunks

        for rank, result in enumerate(
            results,
            start=1
        ):

            print(f"\n--- Retrieved Result {rank} ---")

            print(
                "Similarity:",
                round(
                    result["similarity_score"],
                    4
                )
            )

            print(
                "Retrieved chunk ID:",
                result["chunk_id"]
            )

            print(
                "Retrieved page:",
                result["page_number"]
            )

            print(
                "Retrieved source:",
                result.get(
                    "source",
                    PDF_PATH.name
                )
            )

            print("\nRetrieved content:")

            print(result["content"])

            print("-" * 50)


    # Step 6: Final validation

    print("\n" + "=" * 60)

    print("EMBEDDING RETRIEVAL TEST COMPLETED")

    print("=" * 60)


# =====================================================
# 5. EXECUTION
# =====================================================

if __name__ == "__main__":

    try:

        test_embedding_retrieval()

    except Exception as error:

        print("\nTEST FAILED!")

        print(type(error).__name__, ":", error)

        raise
