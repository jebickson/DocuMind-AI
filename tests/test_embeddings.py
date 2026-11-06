
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_loader import load_pdf
from src.text_splitter import split_text
from src.embeddings import (
    generate_embedding,
    generate_embeddings
)


def test_embedding_pipeline():

    pdf_path = PROJECT_ROOT / "data" / "sample.pdf"

    # Step 1: Extract PDF text
    documents = load_pdf(str(pdf_path))

    # Step 2: Split into chunks
    chunks = split_text(documents)

    print(f"Total chunks: {len(chunks)}")

    # Step 3: Generate embeddings
    vectors = generate_embeddings(chunks)

    print(f"Embedding shape: {vectors.shape}")
    print(f"Embedding dimensions: {vectors.shape[1]}")
    print(f"First 10 values: {vectors[0][:10]}")

    # Step 4: Validate
    assert vectors.shape[0] == len(chunks)
    assert vectors.shape[1] > 0

    # Step 5: Test question embedding
    question = "What is machine learning?"

    question_vector = generate_embedding(question)

    print(f"Question vector shape: {question_vector.shape}")

    assert question_vector.shape[0] == vectors.shape[1]

    print("\nEmbedding engine test successful!")


if __name__ == "__main__":
    test_embedding_pipeline()
