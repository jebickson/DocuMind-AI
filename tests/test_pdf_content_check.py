
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.pdf_loader import load_pdf

pdf_path = PROJECT_ROOT / "data" / "DocuMind_AI_Test_Document.pdf"

documents = load_pdf(str(pdf_path))

print("\n========== PDF CONTENT CHECK ==========")

print("Total pages:", len(documents))

for page in documents:

    print("\nPage:", page.get("page_number"))
    content = page.get("content", "")

    print("Characters:", len(content))
    print("Content:", content[:1500])

    for keyword in [
        "Generative AI",
        "Applications",
        "Local AI",
        "Advantages"
    ]:
        if keyword.lower() in content.lower():
            print("FOUND:", keyword)

print("\n========== CHECK COMPLETED ==========")

