
import re

from src.embeddings import generate_embedding
from src.vector_store import search_vectors


# ============================================================
# DOCUMIND AI - RETRIEVAL CONFIGURATION
# ============================================================

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an",
    "of", "in", "for", "to", "and", "or",
    "how", "does", "do", "explain", "describe",
    "list", "give", "me", "about", "this",
    "that", "with", "from", "which", "when",
    "where", "why", "who"
}

CANDIDATE_MULTIPLIER = 5
MAX_CANDIDATES = 30

SEMANTIC_WEIGHT = 0.75
KEYWORD_WEIGHT = 0.25


# ============================================================
# 1. TOKENIZATION
# ============================================================

def tokenize(text: str) -> set:
    """Convert text into searchable keywords."""

    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower()
    )

    return {
        word for word in words
        if word not in STOP_WORDS and len(word) > 1
    }


# ============================================================
# 2. KEYWORD OVERLAP
# ============================================================

def calculate_keyword_overlap(
    question: str,
    content: str
) -> float:
    """Calculate keyword matching between question and chunk."""

    question_words = tokenize(question)
    content_words = tokenize(content)

    if not question_words:
        return 0.0

    matched_words = question_words.intersection(content_words)

    return len(matched_words) / len(question_words)


# ============================================================
# 3. CALCULATE HYBRID SCORE
# ============================================================

def calculate_hybrid_score(
    similarity: float,
    keyword_score: float
) -> float:
    """Combine semantic and keyword relevance."""

    return (
        SEMANTIC_WEIGHT * similarity
        + KEYWORD_WEIGHT * keyword_score
    )


# ============================================================
# 4. EXPAND NEIGHBORING CHUNKS
# ============================================================

def expand_neighboring_chunks(
    results: list,
    chunks: list,
    window: int = 1
) -> list:
    """
    Add nearby chunks from the same PDF page.

    This helps recover information split across
    adjacent chunks.

    Chunk IDs must be unique and sequential, as assigned
    in the current app.py processing function.
    """

    if not results or not chunks:
        return results

    chunk_positions = {}

    for position, chunk in enumerate(chunks):

        chunk_id = chunk.get("chunk_id")

        if chunk_id is not None:
            chunk_positions[str(chunk_id)] = position

    selected = {}

    for result in results:

        chunk_id = result.get("chunk_id")

        position = chunk_positions.get(str(chunk_id))

        if position is None:
            continue

        source = result.get("source")
        page_number = result.get("page_number")

        start = max(0, position - window)
        end = min(len(chunks), position + window + 1)

        for neighbor_position in range(start, end):

            neighbor = chunks[neighbor_position]

            # Keep expansion within the same PDF and page.
            if neighbor.get("source") != source:
                continue

            if neighbor.get("page_number") != page_number:
                continue

            neighbor_id = str(
                neighbor.get("chunk_id", neighbor_position)
            )

            if neighbor_id in selected:
                continue

            selected[neighbor_id] = {
                **neighbor,
                "similarity_score": result.get(
                    "similarity_score", 0.0
                ),
                "keyword_overlap": calculate_keyword_overlap(
                    "",
                    neighbor.get("content", "")
                ),
                "combined_score": result.get(
                    "combined_score", 0.0
                ),
                "is_neighbor": neighbor_id != str(chunk_id)
            }

    # Preserve original retrieved results and add neighbors.
    # Original retrieval scores are restored below.
    for result in results:

        key = str(result.get("chunk_id"))

        if key in selected:
            selected[key] = {
                **selected[key],
                **result,
                "is_neighbor": False
            }

    return list(selected.values())


# ============================================================
# 5. HYBRID RETRIEVAL
# ============================================================

def retrieve_context(
    question: str,
    index,
    chunks: list,
    top_k: int = 5
) -> list:
    """
    Hybrid retrieval:

    1. Generate question embedding.
    2. Retrieve semantic candidates using FAISS.
    3. Calculate keyword overlap.
    4. Combine semantic and keyword scores.
    5. Rerank candidates.
    6. Expand neighboring chunks.
    """

    if not question or not question.strip():
        raise ValueError("Question cannot be empty.")

    if top_k <= 0:
        raise ValueError("top_k must be positive.")

    if index is None or index.ntotal == 0:
        return []

    if index.ntotal != len(chunks):
        raise ValueError("Index and metadata mismatch.")

    # --------------------------------------------------------
    # Step 1: Generate question embedding
    # --------------------------------------------------------

    question_vector = generate_embedding(question)

    # --------------------------------------------------------
    # Step 2: Retrieve semantic candidates
    # --------------------------------------------------------

    candidate_k = min(
        MAX_CANDIDATES,
        max(top_k * CANDIDATE_MULTIPLIER, top_k),
        index.ntotal
    )

    candidates = search_vectors(
        index=index,
        chunks=chunks,
        query_embedding=question_vector,
        top_k=candidate_k
    )

    if not candidates:
        return []

    # --------------------------------------------------------
    # Step 3: Calculate hybrid scores
    # --------------------------------------------------------

    for result in candidates:

        similarity = float(
            result.get("similarity_score", 0.0)
        )

        keyword_score = calculate_keyword_overlap(
            question,
            result.get("content", "")
        )

        result["keyword_overlap"] = keyword_score

        result["combined_score"] = calculate_hybrid_score(
            similarity,
            keyword_score
        )

        result["is_neighbor"] = False

    # --------------------------------------------------------
    # Step 4: Rank candidates
    # --------------------------------------------------------

    candidates.sort(
        key=lambda item: item["combined_score"],
        reverse=True
    )

    # Keep the strongest semantic matches as seed chunks.
    seed_results = candidates[:top_k]

    # --------------------------------------------------------
    # Step 5: Expand neighboring chunks
    # --------------------------------------------------------

    expanded_results = expand_neighboring_chunks(
        results=seed_results,
        chunks=chunks,
        window=1
    )

    # --------------------------------------------------------
    # Step 6: Sort expanded results
    # --------------------------------------------------------

    expanded_results.sort(
        key=lambda item: item["combined_score"],
        reverse=True
    )

    return expanded_results


# ============================================================
# 6. FORMAT RETRIEVED CONTEXT
# ============================================================

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
Combined Score: {result.get("combined_score", 0):.4f}

Content:
{result.get("content", "")}
""".strip()
        )

    return "\n\n---\n\n".join(context_parts)


# ============================================================
# END OF DOCUMIND AI RETRIEVER
# ============================================================
