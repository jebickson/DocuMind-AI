import json
import re
from typing import Any, Dict, List, Set

import ollama


# ============================================================
# DOCUMIND AI - SEMANTIC ANSWER VALIDATION
# ============================================================

MODEL_NAME = "llama3.2:1b"

NO_INFORMATION = (
    "I could not find this information "
    "in the uploaded PDF."
)

MAX_CLAIMS_TO_VERIFY = 20
MAX_EVIDENCE_CHARS = 2500

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an", "of", "in", "for",
    "to", "and", "or", "how", "does", "do", "explain", "describe",
    "list", "give", "me", "about", "this", "that", "with", "from",
    "which", "when", "where", "why", "who", "it", "its", "can",
    "be", "as", "by", "on", "into", "then", "than", "there",
}

META_PATTERNS = [
    r"^note that i have",
    r"^i have not added",
    r"^i did not add",
    r"^i have not invented",
    r"^i did not invent",
    r"^i hope this helps",
    r"^let me know if",
    r"^based on the provided pdf context",
    r"^according to the supplied context",
    r"^i will answer your question",
    r"^here is the answer",
    r"^the answer is based on",
    r"^i cannot provide",
]


# ============================================================
# 1. PAGE CITATION HELPERS
# ============================================================

def get_available_pages(results: List[Dict[str, Any]]) -> Set[str]:
    """Return page numbers represented in retrieved chunks."""
    return {
        str(result["page_number"])
        for result in results
        if result.get("page_number") is not None
    }


def extract_cited_pages(answer: str) -> Set[str]:
    """Extract simple page citations such as 'Page: 3' or 'PDF page 3'."""
    pattern = r"\b(?:PDF\s+)?pages?\s*[:#]?\s*(\d+)\b"
    return set(re.findall(pattern, answer, flags=re.IGNORECASE))


# ============================================================
# 2. TEXT AND CLAIM HELPERS
# ============================================================

def tokenize(text: str) -> Set[str]:
    """Extract meaningful keywords from text."""
    words = re.findall(r"\b[a-zA-Z0-9]+\b", text.lower())
    return {
        word for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


def is_meta_statement(text: str) -> bool:
    """Filter commentary about the AI's own response."""
    cleaned = re.sub(r"^[\W\d_]+", "", text.strip())
    return any(
        re.search(pattern, cleaned, flags=re.IGNORECASE)
        for pattern in META_PATTERNS
    )


def extract_claims(answer: str) -> List[str]:
    """Split an answer into sentence-like claims."""
    if not answer:
        return []

    claims = []

    for line in answer.splitlines():
        line = line.strip()
        if not line:
            continue

        line = re.sub(r"^#{1,6}\s*", "", line)
        line = re.sub(r"^[-*•]\s*", "", line)
        line = re.sub(r"^\d+[.)]\s*", "", line)
        line = line.strip()

        if not line:
            continue

        if re.fullmatch(r"\[Source:.*?\]", line, flags=re.IGNORECASE):
            continue

        for sentence in re.split(r"(?<=[.!?])\s+", line):
            sentence = re.sub(
                r"\[Source:.*?\]", "", sentence, flags=re.IGNORECASE
            ).strip()

            if len(tokenize(sentence)) >= 2 and not is_meta_statement(sentence):
                claims.append(sentence)

    return claims


# ============================================================
# 3. SELECT PDF EVIDENCE FOR A CLAIM
# ============================================================

def find_best_evidence(
    claim: str,
    results: List[Dict[str, Any]],
    top_n: int = 2,
) -> List[Dict[str, Any]]:
    """Rank retrieved chunks by keyword overlap to select candidate evidence."""
    claim_words = tokenize(claim)

    if not claim_words or not results:
        return []

    ranked = []

    for result in results:
        content = result.get("content", "")
        content_words = tokenize(content)
        matched = claim_words.intersection(content_words)
        score = len(matched) / len(claim_words)

        ranked.append({
            "score": score,
            "matched_keywords": sorted(matched),
            "evidence": content,
            "source": result.get("source", "Uploaded PDF"),
            "page_number": result.get("page_number"),
            "chunk_id": result.get("chunk_id"),
        })

    ranked.sort(key=lambda item: item["score"], reverse=True)
    return ranked[:top_n]


# ============================================================
# 4. OLLAMA SEMANTIC VERIFICATION
# ============================================================

def verify_claim_with_ollama(
    claim: str,
    evidence_items: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Ask Ollama whether the supplied PDF passages support the claim."""
    if not evidence_items:
        return {
            "semantic_status": "insufficient_evidence",
            "reason": "No retrieved PDF passage was available.",
            "verification_method": "no_evidence",
        }

    evidence_blocks = []

    for number, item in enumerate(evidence_items, start=1):
        passage = (item.get("evidence") or "")[:MAX_EVIDENCE_CHARS]
        evidence_blocks.append(
            f"PASSAGE {number}\n"
            f"Source: {item.get('source')}\n"
            f"Page: {item.get('page_number')}\n"
            f"Text:\n{passage}"
        )

    evidence_text = "\n\n---\n\n".join(evidence_blocks)

    prompt = f"""
You are an evidence-checking component for a PDF question-answering system.

Decide whether the PDF evidence supports the claim.

Use ONLY the evidence passages below. Do not use outside knowledge.
A shared keyword is NOT enough to establish support.
A claim is supported only when the evidence directly states it or clearly entails it.
A claim is contradicted only when the evidence clearly states the opposite.
If the passages do not establish either conclusion, use insufficient_evidence.
Do not treat missing information as contradiction.

CLAIM:
{claim}

PDF EVIDENCE:
{evidence_text}

Return only a JSON object with exactly these keys:
{{
  "verdict": "supported",
  "reason": "Short explanation based only on the passages"
}}

The verdict must be exactly one of:
supported, contradicted, insufficient_evidence
"""

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a cautious evidence verifier. "
                    "Never invent evidence. Return valid JSON only."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        format="json",
        options={
            "temperature": 0,
            "top_p": 0.5,
            "num_predict": 150,
            "num_ctx": 8192,
        },
    )

    raw_content = (
        response.get("message", {}).get("content", "") or ""
    ).strip()

    parsed = json.loads(raw_content)
    verdict = str(parsed.get("verdict", "")).strip().lower()

    allowed = {
        "supported",
        "contradicted",
        "insufficient_evidence",
    }

    if verdict not in allowed:
        raise ValueError(
            f"Ollama returned an unexpected verdict: {verdict!r}"
        )

    return {
        "semantic_status": verdict,
        "reason": str(parsed.get("reason", "")).strip(),
        "verification_method": "ollama",
    }


# ============================================================
# 5. VERIFY ALL CLAIMS
# ============================================================

def verify_claims(
    answer: str,
    results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Verify extracted claims against their best candidate passages."""
    verification_results = []
    claims = extract_claims(answer)

    for claim in claims[:MAX_CLAIMS_TO_VERIFY]:
        evidence_items = find_best_evidence(claim, results, top_n=2)

        try:
            semantic = verify_claim_with_ollama(
                claim,
                evidence_items,
            )

            semantic_status = semantic["semantic_status"]
            reason = semantic["reason"]
            method = semantic["verification_method"]

        except Exception as error:
            # Keep the app usable if Ollama is stopped, the model is
            # missing, or the model returns invalid JSON.
            semantic_status = "verification_error"
            reason = (
                "Local semantic verification failed. "
                f"Check that Ollama and {MODEL_NAME} are available. "
                f"Details: {error}"
            )
            method = "verification_error"

        best_evidence = evidence_items[0] if evidence_items else {
            "score": 0.0,
            "matched_keywords": [],
            "evidence": "",
            "source": None,
            "page_number": None,
        }

        if semantic_status == "supported":
            app_status = "supported"
        elif semantic_status == "contradicted":
            app_status = "unsupported"
        else:
            # Includes insufficient_evidence and verification_error.
            app_status = "uncertain"

        verification_results.append({
            "claim": claim,
            "status": app_status,
            "semantic_status": semantic_status,
            "reason": reason,
            "verification_method": method,
            "score": round(best_evidence["score"], 3),
            "matched_keywords": best_evidence["matched_keywords"],
            "evidence": best_evidence["evidence"],
            "source": best_evidence["source"],
            "page_number": best_evidence["page_number"],
            "evidence_passages": [item["evidence"] for item in evidence_items], # ALIGNED WITH UI
        })

    if len(claims) > MAX_CLAIMS_TO_VERIFY:
        verification_results.append({
            "claim": (
                f"{len(claims) - MAX_CLAIMS_TO_VERIFY} additional "
                "claims were not checked because of the per-answer limit."
            ),
            "status": "uncertain",
            "semantic_status": "not_checked",
            "reason": "Increase MAX_CLAIMS_TO_VERIFY if needed.",
            "verification_method": "not_checked",
            "score": 0.0,
            "matched_keywords": [],
            "evidence": "",
            "source": None,
            "page_number": None,
            "evidence_passages": [],
        })

    return verification_results


# ============================================================
# 6. VALIDATE THE COMPLETE ANSWER
# ============================================================

def validate_answer(
    answer: str,
    results: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Preserve the existing validate_answer(answer, results) interface."""
    warnings = []

    if not answer or not answer.strip():
        return {
            "valid": False,
            "answer": "",
            "warnings": ["AI generated an empty answer."],
            "available_pages": [],
            "cited_pages": [],
            "claim_verification": [],
        }

    answer = answer.strip()

    if answer == NO_INFORMATION:
        return {
            "valid": True,
            "answer": answer,
            "warnings": [],
            "available_pages": sorted(get_available_pages(results)),
            "cited_pages": [],
            "claim_verification": [],
        }

    if not results:
        return {
            "valid": False,
            "answer": NO_INFORMATION,
            "warnings": ["No PDF chunks were retrieved."],
            "available_pages": [],
            "cited_pages": [],
            "claim_verification": [],
        }

    available_pages = get_available_pages(results)
    cited_pages = extract_cited_pages(answer)
    invalid_pages = cited_pages - available_pages

    if invalid_pages:
        warnings.append(
            "Answer contains page references not present "
            f"in retrieved chunks: {sorted(invalid_pages)}"
        )

    if not cited_pages:
        print("Debug: No page citations found in answer.")

    claim_verification = verify_claims(answer, results)

    contradicted_count = sum(
        item["semantic_status"] == "contradicted"
        for item in claim_verification
    )
    insufficient_count = sum(
        item["semantic_status"] == "insufficient_evidence"
        for item in claim_verification
    )
    error_count = sum(
        item["semantic_status"] == "verification_error"
        for item in claim_verification
    )

    if contradicted_count:
        warnings.append(
            f"{contradicted_count} claim(s) appear to conflict "
            "with the retrieved PDF evidence."
        )

    if insufficient_count:
        warnings.append(
            f"{insufficient_count} claim(s) lack sufficient "
            "retrieved evidence."
        )

    if error_count:
        warnings.append(
            f"Semantic verification failed for {error_count} claim(s). "
            "Check Ollama and the local model."
        )

    is_valid = (
        len(warnings) == 0
        and len(claim_verification) > 0
    )

    return {
        "valid": is_valid,
        "answer": answer,
        "warnings": warnings,
        "available_pages": sorted(available_pages),
        "cited_pages": sorted(cited_pages),
        "claim_verification": claim_verification,
    }