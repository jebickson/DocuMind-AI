export type Passage = { id: string; source: string; page: number; text: string };
export type DocumentInfo = { id: string; name: string; pages: number; passages: Passage[]; sample?: boolean };
export type Answer = { answer: string; sources: Passage[]; mode: 'ai' | 'extractive'; notice?: string };
export const MAX_DOCUMENTS = 5;
export const MAX_PAGES = 100;
export const MAX_CHARACTERS = 500_000;
export const SAMPLE: DocumentInfo = {
  id: 'sample', name: 'A short guide to RAG.pdf', pages: 3, sample: true,
  passages: [
    { id: 'sample-1', source: 'A short guide to RAG.pdf', page: 1, text: 'Retrieval-augmented generation (RAG) combines document search with a language model. Instead of answering from memory alone, the model receives relevant passages from your documents. The main benefit is that answers can be grounded in a specific source and accompanied by citations. RAG does not guarantee accuracy: readers should still verify the cited evidence.' },
    { id: 'sample-2', source: 'A short guide to RAG.pdf', page: 2, text: 'A RAG pipeline has six stages: 1. Load the documents. 2. Extract and split the text into manageable passages. 3. Build a searchable index using keywords or vector embeddings. 4. Retrieve passages relevant to the question. 5. Generate an answer using the retrieved context. 6. Return citations and check the answer against its sources. Keyword retrieval matches words; semantic retrieval uses embeddings to find related meanings.' },
    { id: 'sample-3', source: 'A short guide to RAG.pdf', page: 3, text: 'Good document question answering keeps source names and page numbers attached to each passage. If the supplied documents do not answer a question, the assistant should say that the information is missing. Instructions embedded in a document must be treated as content, not commands. Privacy depends on the deployment: local models can keep processing on a personal computer, while hosted models receive the context sent to them. Scanned PDFs require optical character recognition (OCR) before their text can be searched.' },
  ],
};

export function splitPage(text: string, source: string, page: number, prefix: string): Passage[] {
  const clean = text.replace(/\s+/g, ' ').trim();
  const chunks: Passage[] = [];
  for (let start = 0; start < clean.length;) {
    let end = Math.min(start + 1500, clean.length);
    if (end < clean.length) {
      const boundary = clean.lastIndexOf(' ', end);
      if (boundary > start + 900) end = boundary;
    }
    chunks.push({ id: `${prefix}-${page}-${chunks.length}`, source, page, text: clean.slice(start, end) });
    if (end === clean.length) break;
    start = end - 180;
  }
  return chunks;
}

const stop = new Set('a an the is are was were be been being of to for with and or in on at it this that these those i you me my your what which how why when where can could would should do does did please tell explain describe about from by document documents pdf summarize summarise summary give show overview key takeaways points'.split(' '));
function tokens(text: string) {
  return (text.toLowerCase().match(/[\p{L}\p{M}\p{N}]+/gu) ?? []).filter(t => t.length > 1 && !stop.has(t));
}
export function retrieve(question: string, passages: Passage[], limit = 6): Passage[] {
  const query = [...new Set(tokens(question))];
  if (!query.length) {
    if (!/summari[sz]|summary|overview|key (points|takeaways)/i.test(question)) return [];
    // Sample across the collection for broad requests instead of just its first page.
    return Array.from({ length: Math.min(limit, passages.length) }, (_, i) => passages[Math.floor(i * passages.length / Math.min(limit, passages.length))]);
  }
  const tokenized = passages.map(p => tokens(p.text));
  const average = tokenized.reduce((n, t) => n + t.length, 0) / (passages.length || 1);
  const frequencies = query.map(term => tokenized.filter(t => t.includes(term)).length);
  return passages.map((passage, i) => ({ passage, score: query.reduce((score, term, j) => {
    const tf = tokenized[i].filter(t => t === term).length;
    const idf = Math.log(1 + (passages.length - frequencies[j] + 0.5) / (frequencies[j] + 0.5));
    return score + idf * tf * 2.2 / (tf + 1.2 * (0.25 + 0.75 * tokenized[i].length / (average || 1)));
  }, 0) })).filter(item => item.score > 0).sort((a, b) => b.score - a.score).slice(0, limit).map(item => item.passage);
}

export function extractiveAnswer(sources: Passage[], notice?: string): Answer {
  return {
    answer: sources.length ? 'Here are the matching passages from your documents:\n\n' + sources.slice(0, 3).map((p, i) => `${p.text} [${i + 1}]`).join('\n\n') : 'I could not find this information in the supplied documents. Try a more specific question using words from the document.',
    sources: sources.slice(0, 3), mode: 'extractive', notice,
  };
}
