
import re

from src.embeddings import generate_embedding
from src.vector_store import search_vectors


STOP_WORDS = {
    "what", "is", "are", "the", "a", "an",
    "of", "in", "for", "to", "and", "or",
    "how", "does", "do", "explain", "describe",
    "list", "give", "me", "about"
}


def tokenize(text: str) -> set:
    """Convert text into searchable keywords."""

    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())

    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


def calculate_keyword_overlap(question: str, content: str) -> float:
    """Calculate keyword matching between question and chunk."""

    question_words = tokenize(question)
    content_words = tokenize(content)

    if not question_words:
        return 0.0

    matched_words = question_words.intersection(content_words)

    return len(matched_words) / len(question_words)


def retrieve_context(
    question: str,
    index,
    chunks: list,
    top_k: int = 3
) -> list:
    """
    Hybrid retrieval:
    1. Generate question embedding.
    2. Retrieve semantic candidates using FAISS.
    3. Calculate keyword overlap.
    4. Combine scores.
    5. Rerank relevant chunks.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    if index.ntotal == 0:
        return []

    if index.ntotal != len(chunks):
        raise ValueError("Index and metadata mismatch.")

    # Step 1: Generate question embedding
    question_vector = generate_embedding(question)

    # Step 2: Retrieve a larger candidate pool
    candidate_k = min(15, index.ntotal)

    candidates = search_vectors(
        index=index,
        chunks=chunks,
        query_embedding=question_vector,
        top_k=candidate_k
    )

    # Step 3: Calculate hybrid scores
    for result in candidates:

        similarity = result["similarity_score"]

        keyword_score = calculate_keyword_overlap(
            question,
            result["content"]
        )

        result["keyword_overlap"] = keyword_score

        # Combined semantic and keyword score
        result["combined_score"] = (
            0.75 * similarity +
            0.25 * keyword_score
        )

    # Step 4: Rank candidates
    candidates.sort(
        key=lambda item: item["combined_score"],
        reverse=True
    )

    # Step 5: Return top relevant chunks
    return candidates[:top_k]


def format_context(results: list) -> str:
    """Format retrieved chunks for the LLM."""

    if not results:
        return "No relevant information found."

    context_parts = []

    for result in results:

        context_parts.append(
            f"""
Source: {result.get("source", "Uploaded PDF")}
PDF Page: {result.get("page_number", "Unknown")}
Chunk ID: {result.get("chunk_id", "Unknown")}
Similarity: {result.get("similarity_score", 0):.4f}
Keyword Overlap: {result.get("keyword_overlap", 0):.4f}

Content:
{result["content"]}
"""
        )

    return "\n---\n".join(context_parts)
