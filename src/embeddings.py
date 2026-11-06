
import ollama
import numpy as np


MODEL_NAME = "nomic-embed-text"


def generate_embedding(text: str) -> np.ndarray:
    """
    Generate an embedding for a user search query.
    """

    if not text or not text.strip():
        raise ValueError("Query cannot be empty.")

    response = ollama.embed(
        model=MODEL_NAME,
        input=f"search_query: {text.strip()}"
    )

    embedding = np.asarray(
        response["embeddings"][0],
        dtype=np.float32
    )

    if embedding.shape != (768,):
        raise ValueError(
            f"Unexpected query embedding shape: {embedding.shape}"
        )

    return embedding


def generate_embeddings(chunks: list) -> np.ndarray:
    """
    Generate embeddings for PDF document chunks.
    """

    if not chunks:
        raise ValueError("No document chunks provided.")

    texts = []

    for chunk in chunks:

        content = chunk.get("content", "")

        if not content.strip():
            raise ValueError("Empty document chunk found.")

        texts.append(
            f"search_document: {content.strip()}"
        )

    response = ollama.embed(
        model=MODEL_NAME,
        input=texts
    )

    embeddings = np.asarray(
        response["embeddings"],
        dtype=np.float32
    )

    if embeddings.shape != (len(chunks), 768):
        raise ValueError(
            f"Unexpected embedding shape: {embeddings.shape}"
        )

    if not np.isfinite(embeddings).all():
        raise ValueError("Invalid embedding values.")

    print(
        f"Generated {len(embeddings)} document embeddings."
    )

    print(
        f"Embedding dimensions: {embeddings.shape[1]}"
    )

    return embeddings
