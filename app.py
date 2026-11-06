
import streamlit as st
import tempfile
import os
import re

# =====================================================
# DOCUMIND AI - MODULE IMPORTS
# =====================================================

from src.pdf_loader import load_pdf
from src.text_splitter import split_text
from src.embeddings import generate_embeddings
from src.vector_store import create_vector_store
from src.retriever import retrieve_context
from src.llm import generate_answer, build_context
from src.answer_validator import validate_answer


# =====================================================
# 1. PAGE CONFIGURATION
# =====================================================

st.set_page_config(
    page_title="DocuMind AI",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# 2. CUSTOM CSS
# =====================================================

st.markdown("""
<style>

.stApp {
    background-color: #0b1020;
    color: #f8fafc;
}

[data-testid="stSidebar"] {
    background-color: #111827;
    border-right: 1px solid #263247;
}

.main-title {
    font-size: 36px;
    font-weight: 800;
    color: #a78bfa;
}

.subtitle {
    color: #94a3b8;
    font-size: 15px;
}

div[data-testid="stChatMessage"] {
    border: 1px solid #263247;
    border-radius: 12px;
    padding: 12px;
}

.stButton button {
    border-radius: 8px;
}

</style>
""", unsafe_allow_html=True)


# =====================================================
# 3. SESSION STATE
# =====================================================

DEFAULT_STATE = {
    "messages": [],
    "vector_index": None,
    "chunks": [],
    "documents": [],
    "last_results": [],
    "last_question": ""
}

for key, value in DEFAULT_STATE.items():

    if key not in st.session_state:
        st.session_state[key] = value


# =====================================================
# 4. HELPER FUNCTIONS
# =====================================================

STOP_WORDS = {
    "what", "is", "are", "the", "a", "an",
    "of", "in", "on", "to", "for", "and",
    "with", "how", "why", "when", "where",
    "explain", "describe", "tell", "me",
    "about", "give", "list", "please",
    "can", "you", "does", "do", "from"
}


def get_keywords(text):

    words = re.findall(
        r"\b[a-zA-Z0-9]+\b",
        text.lower()
    )

    return {
        word for word in words
        if len(word) > 2 and word not in STOP_WORDS
    }


def calculate_keyword_overlap(question, content):

    question_words = get_keywords(question)

    content_words = get_keywords(content)

    if not question_words:
        return 0.0

    matched = question_words.intersection(content_words)

    return len(matched) / len(question_words)


# =====================================================
# 5. RETRIEVAL VALIDATION
# =====================================================

def validate_retrieval(question, results):
    """
    Basic retrieval relevance screening.

    This is a heuristic, not a guarantee of relevance.
    """

    if not results:
        return False

    best_score = max(
        result["similarity_score"]
        for result in results
    )

    best_overlap = max(
        calculate_keyword_overlap(
            question,
            result["content"]
        )
        for result in results
    )

    if best_score >= 0.65:
        return True

    if best_score >= 0.35 and best_overlap >= 0.25:
        return True

    return False


# =====================================================
# 6. EXTRACT PDF SOURCES
# =====================================================

def get_sources(results):

    sources = []

    seen = set()

    for result in results:

        key = (
            result.get("source", "Uploaded PDF"),
            result.get("page_number", 0)
        )

        if key in seen:
            continue

        seen.add(key)

        sources.append({
            "source": key[0],
            "page_number": key[1],
            "similarity_score": result["similarity_score"]
        })

    return sources


# =====================================================
# 7. DOCUMENT PROCESSING
# =====================================================

def process_documents(uploaded_files):

    all_chunks = []

    processed_names = []

    progress = st.progress(0)

    status = st.empty()

    try:

        for file_number, uploaded_file in enumerate(
            uploaded_files
        ):

            status.write(
                f"Reading {uploaded_file.name}..."
            )

            temp_path = None

            try:

                with tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=".pdf"
                ) as temp_file:

                    temp_file.write(
                        uploaded_file.getvalue()
                    )

                    temp_path = temp_file.name

                # Extract PDF text
                documents = load_pdf(temp_path)

                if not documents:

                    st.warning(
                        f"No readable text in {uploaded_file.name}"
                    )

                    continue

                # Split PDF into chunks
                chunks = split_text(documents)

                for chunk in chunks:

                    chunk["source"] = uploaded_file.name

                    chunk["chunk_id"] = len(all_chunks) + 1

                all_chunks.extend(chunks)

                processed_names.append(
                    uploaded_file.name
                )

            finally:

                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

            progress.progress(
                (file_number + 1) / len(uploaded_files)
            )

        if not all_chunks:

            raise ValueError(
                "No readable PDF text was extracted."
            )

        # Generate embeddings
        status.write("Generating embeddings...")

        embeddings = generate_embeddings(all_chunks)

        # Create FAISS database
        status.write("Building FAISS vector database...")

        index = create_vector_store(
            all_chunks,
            embeddings
        )

        # Update application state
        st.session_state.vector_index = index

        st.session_state.chunks = all_chunks

        st.session_state.documents = processed_names

        st.session_state.messages = []

        st.session_state.last_results = []

        st.session_state.last_question = ""

        progress.progress(1.0)

        status.success(
            f"Successfully processed {len(processed_names)} PDF(s)!"
        )

        return True

    except Exception as error:

        status.empty()

        st.error(
            f"Document processing failed: {error}"
        )

        return False


# =====================================================
# 8. AI QUESTION ANSWERING WITH VALIDATION
# =====================================================

def answer_question(question):

    index = st.session_state.vector_index

    chunks = st.session_state.chunks

    # Step 1: Retrieve relevant PDF chunks
    results = retrieve_context(
        question=question,
        index=index,
        chunks=chunks,
        top_k=5
    )

    st.session_state.last_results = results

    st.session_state.last_question = question

    # Step 2: Validate retrieval
    if not validate_retrieval(question, results):

        return {
            "answer": (
                "I could not find sufficiently relevant "
                "information in the uploaded PDF."
            ),
            "sources": [],
            "validation": {
                "valid": False,
                "answer": (
                    "I could not find sufficiently relevant "
                    "information in the uploaded PDF."
                ),
                "warnings": [
                    "No sufficiently relevant PDF context found."
                ],
                "available_pages": [],
                "cited_pages": []
            }
        }

    # Step 3: Build PDF context
    context = build_context(results)

    if not context.strip():

        return {
            "answer": (
                "I could not find this information "
                "in the uploaded PDF."
            ),
            "sources": [],
            "validation": {
                "valid": False,
                "answer": (
                    "I could not find this information "
                    "in the uploaded PDF."
                ),
                "warnings": ["Retrieved context is empty."],
                "available_pages": [],
                "cited_pages": []
            }
        }

    # Step 4: Generate answer using Ollama
    answer = generate_answer(
        question=question,
        context=context
    )

    # Step 5: Validate generated answer
    validation = validate_answer(
        answer=answer,
        results=results
    )

    # Step 6: Prepare PDF sources
    sources = get_sources(results)

    # Step 7: Return complete response
    return {
        "answer": validation["answer"],
        "sources": sources,
        "validation": validation
    }


# =====================================================
# 9. SIDEBAR
# =====================================================

with st.sidebar:

    st.markdown("## 📚 DocuMind AI")

    st.caption(
        "Offline PDF Intelligence Assistant"
    )

    st.divider()

    st.markdown("### Upload Documents")

    uploaded_files = st.file_uploader(
        "Choose PDF documents",
        type=["pdf"],
        accept_multiple_files=True
    )

    process_button = st.button(
        "⚡ Process Documents",
        use_container_width=True,
        type="primary",
        disabled=not uploaded_files
    )

    if process_button:

        process_documents(uploaded_files)

    st.divider()

    st.markdown("### Your Documents")

    if st.session_state.documents:

        for document in st.session_state.documents:

            st.markdown(
                f"📄 {document}"
            )

        st.caption(
            f"{len(st.session_state.chunks)} chunks indexed"
        )

    else:

        st.info("No documents uploaded yet.")

    st.divider()

    # Clear chat
    if st.button(
        "🗑️ Clear Chat",
        use_container_width=True
    ):

        st.session_state.messages = []

        st.session_state.last_results = []

        st.session_state.last_question = ""

        st.rerun()

    # Reset documents
    if st.button(
        "Reset Documents",
        use_container_width=True
    ):

        st.session_state.vector_index = None

        st.session_state.chunks = []

        st.session_state.documents = []

        st.session_state.messages = []

        st.session_state.last_results = []

        st.session_state.last_question = ""

        st.rerun()

    st.divider()

    st.markdown("### System Information")

    st.caption("LLM: Ollama")

    st.caption("Model: Llama 3.2 1B")

    st.caption("Embeddings: Nomic")

    st.caption("Vector DB: FAISS")

    st.caption("Language: Python 3")

    st.markdown("---")

    st.caption(
        "Powered by Local AI • DocuMind AI"
    )


# =====================================================
# 10. MAIN DASHBOARD
# =====================================================

st.markdown(
    '<div class="main-title">DocuMind AI 📚</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Your private, offline AI document assistant.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()


# =====================================================
# 11. DASHBOARD METRICS
# =====================================================

col1, col2, col3 = st.columns(3)

with col1:

    st.metric(
        "Documents",
        len(st.session_state.documents)
    )

with col2:

    st.metric(
        "Text Chunks",
        len(st.session_state.chunks)
    )

with col3:

    st.metric(
        "AI Model",
        "Llama 3.2 1B"
    )

st.divider()


# =====================================================
# 12. WELCOME SCREEN
# =====================================================

if st.session_state.vector_index is None:

    st.markdown("## Welcome to DocuMind AI")

    st.write(
        "Upload your PDF documents and ask questions "
        "using your local AI assistant."
    )

    st.info(
        "Upload PDF documents from the sidebar "
        "and click Process Documents to begin."
    )

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown("### 📄 PDF Reader")

        st.caption(
            "Extract text from PDF documents."
        )

    with col2:

        st.markdown("### 🧠 Local AI")

        st.caption(
            "Generate answers with Ollama."
        )

    with col3:

        st.markdown("### 🔍 Semantic Search")

        st.caption(
            "Find relevant document passages."
        )


# =====================================================
# 13. CHAT HISTORY
# =====================================================

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])

        # Display validation status
        validation = message.get("validation")

        if validation:

            if validation.get("valid"):

                st.caption(
                    "✓ Citation consistency check passed"
                )

            else:

                st.caption(
                    "⚠ Answer validation warnings"
                )

                for warning in validation.get("warnings", []):

                    st.caption(f"• {warning}")

        # Display PDF sources
        if message.get("sources"):

            with st.expander("📚 View PDF Sources"):

                for source in message["sources"]:

                    st.markdown(
                        f"**{source['source']}** "
                        f"— Page {source['page_number']}"
                    )

                    st.caption(
                        "Similarity: "
                        f"{source['similarity_score']:.4f}"
                    )


# =====================================================
# 14. CHAT INPUT WITH ANSWER VALIDATION
# =====================================================

if st.session_state.vector_index is not None:

    question = st.chat_input(
        "Ask anything about your uploaded PDFs..."
    )

    if question:

        # Save user question
        st.session_state.messages.append({

            "role": "user",

            "content": question

        })

        with st.chat_message("user"):

            st.markdown(question)

        # Generate assistant response
        with st.chat_message("assistant"):

            try:

                with st.spinner(
                    "Searching PDFs and generating answer..."
                ):

                    response = answer_question(question)

                answer = response["answer"]

                sources = response["sources"]

                validation = response["validation"]

                # Step 1: Display validation status
                if validation["valid"]:

                    st.success(
                        "Answer validation successful!"
                    )

                else:

                    st.warning(
                        "Answer validation warnings"
                    )

                    for warning in validation["warnings"]:

                        st.write(f"- {warning}")

                # Step 2: Display final answer
                st.markdown(answer)

                # Step 3: Display PDF sources
                if sources:

                    with st.expander(
                        "📚 View PDF Sources"
                    ):

                        for source in sources:

                            st.markdown(
                                f"**{source['source']}** "
                                f"— Page {source['page_number']}"
                            )

                            st.caption(
                                "Similarity: "
                                f"{source['similarity_score']:.4f}"
                            )

                # Step 4: Save assistant response
                st.session_state.messages.append({

                    "role": "assistant",

                    "content": answer,

                    "sources": sources,

                    "validation": validation

                })

            except Exception as error:

                error_message = (
                    f"An error occurred: {error}"
                )

                st.error(error_message)

                st.session_state.messages.append({

                    "role": "assistant",

                    "content": error_message,

                    "sources": [],

                    "validation": {
                        "valid": False,
                        "warnings": [str(error)]
                    }

                })


# =====================================================
# 15. RETRIEVAL DEBUGGING PANEL
# =====================================================

if st.session_state.last_results:

    st.divider()

    with st.expander(
        "🔍 Debug: Retrieved PDF Chunks",
        expanded=False
    ):

        st.markdown("### Retrieval Analysis")

        for number, result in enumerate(
            st.session_state.last_results,
            start=1
        ):

            st.markdown(
                f"#### Retrieved Chunk {number}"
            )

            st.write(
                "**Source:**",
                result.get("source", "Uploaded PDF")
            )

            st.write(
                "**Page:**",
                result.get("page_number", "Unknown")
            )

            st.write(
                "**Chunk ID:**",
                result.get("chunk_id", "Unknown")
            )

            st.write(
                "**Similarity Score:**",
                round(
                    result["similarity_score"],
                    4
                )
            )

            st.write(
                "**Keyword Overlap:**",
                round(
                    result.get(
                        "keyword_overlap",
                        calculate_keyword_overlap(
                            st.session_state.last_question,
                            result["content"]
                        )
                    ),
                    4
                )
            )

            if "combined_score" in result:

                st.write(
                    "**Combined Score:**",
                    round(result["combined_score"], 4)
                )

            st.markdown("**Retrieved Content:**")

            st.write(result["content"])

            st.divider()


# =====================================================
# END OF DOCUMIND AI APPLICATION
# =====================================================
