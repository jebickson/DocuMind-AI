
# =====================================================
# DOCUMIND AI - TEXT SPLITTER
# =====================================================

from typing import List, Dict


# Chunk configuration
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def split_text(documents: List[Dict]) -> List[Dict]:
    """
    Split extracted PDF pages into smaller text chunks.

    Each chunk maintains:
    - Content
    - Page number
    - Chunk ID
    """

    chunks = []

    chunk_id = 1

    for document in documents:

        # Get page content
        text = document.get("content", "")

        page_number = document.get("page_number", 0)

        if not text or not text.strip():
            continue

        # Normalize whitespace
        text = " ".join(text.split())

        # Split into sentences
        sentences = text.replace("? ", "?\n").replace(
            "! ", "!\n"
        ).replace(". ", ".\n").splitlines()

        current_chunk = ""

        for sentence in sentences:

            sentence = sentence.strip()

            if not sentence:
                continue

            # Add sentence to current chunk
            if (
                len(current_chunk) + len(sentence) + 1
                <= CHUNK_SIZE
            ):

                current_chunk += " " + sentence

            else:

                # Save current chunk
                if current_chunk.strip():

                    chunks.append({
                        "content": current_chunk.strip(),
                        "page_number": page_number,
                        "chunk_id": chunk_id
                    })

                    chunk_id += 1

                # Keep overlap from previous chunk
                overlap_text = current_chunk[
                    -CHUNK_OVERLAP:
                ]

                current_chunk = (
                    overlap_text + " " + sentence
                ).strip()

                # Handle exceptionally long sentences
                while len(current_chunk) > CHUNK_SIZE:

                    part = current_chunk[:CHUNK_SIZE]

                    chunks.append({
                        "content": part.strip(),
                        "page_number": page_number,
                        "chunk_id": chunk_id
                    })

                    chunk_id += 1

                    current_chunk = current_chunk[
                        CHUNK_SIZE - CHUNK_OVERLAP:
                    ]

        # Save remaining content
        if current_chunk.strip():

            chunks.append({
                "content": current_chunk.strip(),
                "page_number": page_number,
                "chunk_id": chunk_id
            })

            chunk_id += 1

    print(f"Text splitting successful: {len(chunks)} chunks")

    return chunks
