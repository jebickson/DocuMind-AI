
import json
from pathlib import Path

import faiss
import numpy as np


# =====================================================
# 1. CREATE FAISS VECTOR STORE
# =====================================================

def create_vector_store(chunks, embeddings):

    if len(chunks) == 0:
        raise ValueError("No chunks provided")

    if len(chunks) != len(embeddings):
        raise ValueError("Chunk and embedding count mismatch")

    vectors = np.ascontiguousarray(
        embeddings,
        dtype=np.float32
    )

    if vectors.ndim != 2:
        raise ValueError("Embeddings must be a 2D array")

    if not np.isfinite(vectors).all():
        raise ValueError("Invalid embedding values")

    # Normalize vectors for cosine similarity
    faiss.normalize_L2(vectors)

    dimension = vectors.shape[1]

    index = faiss.IndexFlatIP(dimension)

    index.add(vectors)

    print(
        f"FAISS index created: {index.ntotal} vectors"
    )

    print(
        f"Embedding dimensions: {dimension}"
    )

    return index


# =====================================================
# 2. SAVE VECTOR STORE
# =====================================================

def save_vector_store(
    index,
    chunks,
    save_directory="vector_store"
):

    directory = Path(save_directory)

    directory.mkdir(
        parents=True,
        exist_ok=True
    )

    faiss.write_index(
        index,
        str(directory / "index.faiss")
    )

    with open(
        directory / "metadata.json",
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            chunks,
            file,
            indent=4
        )

    print("Vector database saved successfully!")


# =====================================================
# 3. LOAD VECTOR STORE
# =====================================================

def load_vector_store(
    save_directory="vector_store"
):

    directory = Path(save_directory)

    index_path = directory / "index.faiss"

    metadata_path = directory / "metadata.json"

    if (
        not index_path.exists()
        or not metadata_path.exists()
    ):

        raise FileNotFoundError(
            "Vector database not found"
        )

    index = faiss.read_index(
        str(index_path)
    )

    with open(
        metadata_path,
        "r",
        encoding="utf-8"
    ) as file:

        chunks = json.load(file)

    if index.ntotal != len(chunks):

        raise ValueError(
            "Index and metadata mismatch"
        )

    print("Vector database loaded successfully!")

    return index, chunks


# =====================================================
# 4. SEARCH VECTOR DATABASE
# =====================================================

def search_vectors(
    index,
    chunks,
    query_embedding,
    top_k=3
):

    if top_k <= 0:
        raise ValueError(
            "top_k must be positive"
        )

    if index.ntotal != len(chunks):

        raise ValueError(
            "Index and metadata mismatch"
        )

    if index.ntotal == 0:
        return []

    query = np.asarray(
        query_embedding,
        dtype=np.float32
    ).reshape(1, -1).copy()

    if query.shape[1] != index.d:

        raise ValueError(
            "Embedding dimension mismatch"
        )

    if not np.isfinite(query).all():

        raise ValueError(
            "Invalid query embedding"
        )

    if np.linalg.norm(query) == 0:

        raise ValueError(
            "Query embedding cannot be zero"
        )

    # Normalize query for cosine similarity
    faiss.normalize_L2(query)

    # Search FAISS
    scores, indices = index.search(
        query,
        min(top_k, index.ntotal)
    )

    results = []

    # IMPORTANT: Append each result inside this loop
    for score, idx in zip(
        scores[0],
        indices[0]
    ):

        if idx == -1:
            continue

        chunk = chunks[int(idx)]

        results.append({

            "content": chunk["content"],

            "page_number": chunk["page_number"],

            "chunk_id": chunk["chunk_id"],

            "source": chunk.get(
                "source",
                "Uploaded PDF"
            ),

            "similarity_score": float(score)

        })

    print(
        f"Retrieved {len(results)} chunks "
        f"out of requested {top_k}"
    )

    return results


# =====================================================
# END OF VECTOR STORE
# =====================================================
