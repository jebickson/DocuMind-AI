
import pymupdf
import re


def clean_text(text: str) -> str:
    """Clean unnecessary whitespace from extracted text."""

    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_pdf(pdf_path: str) -> list:
    """
    Extract text from a PDF document.

    Returns:
        List of dictionaries containing page content
        and page numbers.
    """

    documents = []

    try:
        pdf = pymupdf.open(pdf_path)

        if pdf.is_encrypted:
            raise ValueError("Password-protected PDFs are not supported.")

        for page_number, page in enumerate(pdf, start=1):

            text = page.get_text("text")
            text = clean_text(text)

            if not text:
                continue

            documents.append({
                "page_number": page_number,
                "content": text
            })

        pdf.close()

        if not documents:
            raise ValueError(
                "No readable text found in this PDF."
            )

        return documents

    except Exception as error:
        raise RuntimeError(
            f"PDF processing failed: {error}"
        ) from error
