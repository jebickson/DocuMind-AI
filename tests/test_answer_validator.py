
from src.answer_validator import (
    validate_answer,
    NO_INFORMATION
)


# ============================================================
# TEST DATA
# ============================================================

SAMPLE_RESULTS = [
    {
        "source": "test_document.pdf",
        "page_number": 2,
        "chunk_id": 1,
        "content": (
            "Retrieval Augmented Generation combines "
            "information retrieval with generative AI. "
            "It uses retrieved documents to answer questions."
        )
    }
]


# ============================================================
# 1. TEST SUPPORTED CLAIM
# ============================================================

def test_supported_claim():

    answer = (
        "Retrieval Augmented Generation combines "
        "information retrieval with generative AI.\n"
        "[Source: test_document.pdf, Page: 2]"
    )

    result = validate_answer(answer, SAMPLE_RESULTS)

    assert result["valid"] is True

    claims = result["claim_verification"]

    assert len(claims) >= 1
    assert claims[0]["status"] == "supported"

    print("Supported claim test passed!")


# ============================================================
# 2. TEST UNCERTAIN CLAIM
# ============================================================


def test_uncertain_claim():

    answer = (
        "Retrieval explains knowledge systems.\n"
        "[Source: test_document.pdf, Page: 2]"
    )

    result = validate_answer(answer, SAMPLE_RESULTS)

    claims = result["claim_verification"]

    assert len(claims) >= 1
    assert claims[0]["status"] == "uncertain"

    print("Uncertain claim test passed!")


# ============================================================
# 3. TEST UNSUPPORTED CLAIM
# ============================================================

def test_unsupported_claim():

    answer = (
        "Quantum computers use superconducting qubits.\n"
        "[Source: test_document.pdf, Page: 2]"
    )

    result = validate_answer(answer, SAMPLE_RESULTS)

    claims = result["claim_verification"]

    assert len(claims) >= 1
    assert claims[0]["status"] == "unsupported"

    print("Unsupported claim test passed!")


# ============================================================
# 4. TEST INVALID PAGE REFERENCE
# ============================================================

def test_invalid_page():

    answer = (
        "Retrieval Augmented Generation combines "
        "information retrieval with generative AI.\n"
        "[Source: test_document.pdf, Page: 9]"
    )

    result = validate_answer(answer, SAMPLE_RESULTS)

    assert result["valid"] is False
    assert "9" in result["cited_pages"]

    print("Invalid page test passed!")


# ============================================================
# 5. TEST EMPTY ANSWER
# ============================================================

def test_empty_answer():

    result = validate_answer(
        "",
        SAMPLE_RESULTS
    )

    assert result["valid"] is False
    assert result["answer"] == ""

    print("Empty answer test passed!")


# ============================================================
# 6. TEST NO INFORMATION RESPONSE
# ============================================================

def test_no_information():

    result = validate_answer(
        NO_INFORMATION,
        SAMPLE_RESULTS
    )

    assert result["valid"] is True
    assert result["claim_verification"] == []

    print("No information test passed!")


# ============================================================
# 7. TEST NO RETRIEVED RESULTS
# ============================================================

def test_no_results():

    result = validate_answer(
        "Some generated answer.",
        []
    )

    assert result["valid"] is False
    assert result["answer"] == NO_INFORMATION

    print("No results test passed!")


# ============================================================
# RUN ALL TESTS
# ============================================================

if __name__ == "__main__":

    test_supported_claim()
    test_uncertain_claim()
    test_unsupported_claim()
    test_invalid_page()
    test_empty_answer()
    test_no_information()
    test_no_results()

    print("\nALL ANSWER VALIDATOR TESTS PASSED!")
