
import re
from typing import List, Dict, Any


# ============================================================
# DOCUMIND AI - ANSWER VALIDATION
# ============================================================

NO_INFORMATION = (
    "I could not find this information "
    "in the uploaded PDF."
)


# ============================================================
# 1. EXTRACT AVAILABLE PDF PAGES
# ============================================================

def get_available_pages(results: List[Dict[str, Any]]) -> set:
    """
    Extract page numbers from retrieved PDF chunks.
    """

    pages = set()

    for result in results:

        page = result.get("page_number")

        if page is not None:
            pages.add(str(page))

    return pages


# ============================================================
# 2. EXTRACT PAGE REFERENCES FROM ANSWER
# ============================================================

def extract_cited_pages(answer: str) -> set:
    """
    Find page references mentioned in the AI answer.
    """

    pattern = r"\b(?:PDF\s+)?pages?\s*[:#]?\s*(\d+)\b"

    matches = re.findall(
        pattern,
        answer,
        flags=re.IGNORECASE
    )

    return set(matches)


# ============================================================
# 3. VALIDATE ANSWER
# ============================================================

def validate_answer(
    answer: str,
    results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate answer quality and PDF page references.

    Note:
    This validates citation consistency, not complete
    semantic or factual correctness.
    """

    warnings = []

    # Check empty answer
    if not answer or not answer.strip():

        return {
            "valid": False,
            "answer": "",
            "warnings": ["AI generated an empty answer."],
            "available_pages": [],
            "cited_pages": []
        }

    answer = answer.strip()

    # Handle no-information response
    if answer == NO_INFORMATION:

        return {
            "valid": True,
            "answer": answer,
            "warnings": [],
            "available_pages": sorted(
                get_available_pages(results)
            ),
            "cited_pages": []
        }

    # Check retrieved results
    if not results:

        return {
            "valid": False,
            "answer": NO_INFORMATION,
            "warnings": ["No PDF chunks were retrieved."],
            "available_pages": [],
            "cited_pages": []
        }

    # Extract page references
    available_pages = get_available_pages(results)
    cited_pages = extract_cited_pages(answer)

    # Find invalid page references
    invalid_pages = cited_pages - available_pages

    if invalid_pages:

        warnings.append(
            "Answer contains page references "
            f"not present in retrieved chunks: "
            f"{sorted(invalid_pages)}"
        )

    # Check missing citations
    if not cited_pages:

        warnings.append(
            "No PDF page references were included."
        )

    # Final validation
    is_valid = len(warnings) == 0

    return {
        "valid": is_valid,
        "answer": answer,
        "warnings": warnings,
        "available_pages": sorted(available_pages),
        "cited_pages": sorted(cited_pages)
    }


# ============================================================
# 4. END OF ANSWER VALIDATOR
# ============================================================
