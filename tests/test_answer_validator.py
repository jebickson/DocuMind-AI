
from src.answer_validator import validate_answer


def test_valid_answer():

    results = [
        {
            "content": "Machine Learning is a subset of AI.",
            "page_number": 1,
            "chunk_id": 1
        }
    ]

    answer = (
        "Machine Learning is a subset of AI. "
        "Source: PDF Page 1."
    )

    result = validate_answer(answer, results)

    assert result["valid"] is True

    print("Valid answer test passed!")


def test_invalid_page():

    results = [
        {
            "content": "Machine Learning is a subset of AI.",
            "page_number": 1,
            "chunk_id": 1
        }
    ]

    answer = (
        "Machine Learning is a subset of AI. "
        "Source: PDF Page 5."
    )

    result = validate_answer(answer, results)

    assert result["valid"] is False

    print("Invalid page test passed!")


def test_empty_answer():

    result = validate_answer("", [])

    assert result["valid"] is False

    print("Empty answer test passed!")


def test_no_information():

    results = []

    answer = (
        "I could not find this information "
        "in the uploaded PDF."
    )

    result = validate_answer(answer, results)

    assert result["valid"] is True

    print("No information test passed!")


if __name__ == "__main__":

    test_valid_answer()
    test_invalid_page()
    test_empty_answer()
    test_no_information()

    print("\nALL ANSWER VALIDATOR TESTS PASSED!")
