# Jebickson AI

A document intelligence project by Jebickson, with a free public PDF explorer and an offline AI edition.

## Public web edition

The Next.js application in `web/` reads PDFs entirely in the browser. Upload up to five PDFs (15 MB and 100 pages each), ask a question, and inspect matching original passages with file names and page references. Try the built-in RAG guide without uploading anything. Conversations can be downloaded as text.

**This edition provides keyword-ranked excerpts, not AI-generated answers.** It needs no API key, database, account, or model credits. PDF data and questions are never uploaded. State lives in memory and clears on refresh. Scanned PDFs need OCR first. Broad overview queries sample passages rather than summarize an entire document.

### Run locally

Requires Node.js 22 or newer.

```sh
cd web
npm ci
npm run dev
```

### Verify

```sh
cd web
npm test
npm run typecheck
npm run build
```

The install/build scripts copy the matching PDF.js worker, CMaps, fonts, and WASM assets into `public/pdfjs/`. These generated files are ignored by Git and served from the same origin.

### Deploy to Vercel

Import this GitHub repository, select the **Next.js** framework, and set **Root Directory** to `web`. Use `npm ci` to install and `npm run build` to build. No environment variables are required. Production should be public; preview protection can remain enabled. Hosting remains subject to your Vercel plan limits; this app makes no paid AI calls.

## Original offline AI edition

The Python app remains available in `app.py` and `src/`. It uses Streamlit, local Ollama (`llama3.2:1b` and `nomic-embed-text`), and FAISS for semantic retrieval. It is independent of the public browser application.

```sh
python -m venv .venv
# Activate the environment using your shell's command.
pip install -r requirements.txt
ollama pull llama3.2:1b
ollama pull nomic-embed-text
streamlit run app.py
```

Legacy Python scripts under `tests/` require local PDFs, an existing vector index, and a running Ollama instance. They are integration exercises, not portable CI checks. The public edition's automated tests are under `web/tests/`.

## Privacy and limitations

- Uploaded documents are isolated to the current browser tab; there is no shared server document store.
- PDF extraction and ranking run locally. Document text is rendered as plain text to avoid executing embedded markup.
- Page references use PDF page order and may differ from printed page labels.
- Keyword retrieval may miss synonyms or context. Read the full PDF when accuracy matters.
- The sample guide is original project demonstration content.
