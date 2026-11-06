
import sys
from pathlib import Path

# Add project root to Python import path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


from src.pdf_loader import load_pdf
from src.text_splitter import split_text


PDF_PATH = "data/sample.pdf"


def test_pdf_processing():

    documents = load_pdf(PDF_PATH)

    print("\nExtracted PDF Pages:")

    for document in documents:
        print(document["page_number"])
        print(document["content"])

    chunks = split_text(documents)

    print("\nGenerated Chunks:")

    for chunk in chunks:
        print(chunk)

    assert len(documents) > 0
    assert len(chunks) > 0

    print("\nPDF processing successful!")


if __name__ == "__main__":
    test_pdf_processing()
