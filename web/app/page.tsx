'use client';

import { useEffect, useRef, useState } from 'react';
import { BookOpen, FileText, Plus, Sparkles, Upload, X, Search, ShieldCheck, CodeXml, MessageSquare, Trash2, Download, LoaderCircle, PanelLeftClose, PanelLeftOpen, Layers, Quote, Send, Check, CircleHelp } from 'lucide-react';
import { MAX_DOCUMENTS, SAMPLE, retrieve, extractiveAnswer, type Answer, type DocumentInfo, type Passage } from '@/lib/documents';
import { readPdf } from '@/lib/pdf';

type Message = { id: string; question: string; response: Answer };
const suggestions = ['Show an overview', 'What are the six stages of RAG?', 'How should I verify an answer?'];

export default function Home() {
  const [documents, setDocuments] = useState<DocumentInfo[]>([]);
  const [messages, setMessages] = useState<Message[]>([]);
  const [question, setQuestion] = useState('');
  const [busy, setBusy] = useState(false);
  const [processing, setProcessing] = useState('');
  const [error, setError] = useState('');
  const [selected, setSelected] = useState<Passage | null>(null);
  const [sidebar, setSidebar] = useState(true);
  const [dragging, setDragging] = useState(false);
  const [help, setHelp] = useState(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const end = useRef<HTMLDivElement>(null);
  const request = useRef<AbortController | null>(null);
  const uploadLock = useRef(false);
  useEffect(() => { if (window.matchMedia('(max-width: 760px)').matches) setSidebar(false); }, []);
  useEffect(() => {
    if (!help) return;
    const previous = document.activeElement as HTMLElement | null;
    function handleKey(event: KeyboardEvent) {
      if (event.key === 'Escape') setHelp(false);
      if (event.key === 'Tab') {
        const controls = document.querySelectorAll<HTMLButtonElement>('.modal button');
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last?.focus(); }
        else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first?.focus(); }
      }
    }
    document.addEventListener('keydown', handleKey);
    return () => { document.removeEventListener('keydown', handleKey); previous?.focus(); };
  }, [help]);
  useEffect(() => { end.current?.scrollIntoView({ behavior: 'smooth', block: 'end' }); }, [messages, busy]);
  useEffect(() => () => request.current?.abort(), []);
  const passages = documents.flatMap(d => d.passages);

  async function upload(files: FileList | File[] | null) {
    if (!files?.length || uploadLock.current || busy) return;
    uploadLock.current = true;
    setError('');
    try {
      if (documents.length + files.length > MAX_DOCUMENTS) throw new Error(`You can add up to ${MAX_DOCUMENTS} PDFs. Remove a document to make room.`);
      const additions: DocumentInfo[] = [];
      for (const file of Array.from(files)) {
        setProcessing(`Reading ${file.name}…`);
        additions.push(await readPdf(file));
      }
      setDocuments(previous => [...previous, ...additions]);
      if (window.matchMedia('(max-width: 760px)').matches) setSidebar(false);
      setSelected(null);
    } catch (error) { setError(error instanceof Error ? error.message : 'This PDF could not be read. Try another file.'); }
    finally { setProcessing(''); uploadLock.current = false; if (fileInput.current) fileInput.current.value = ''; }
  }

  async function sample() {
    if (busy || processing) return;
    if (!documents.some(d => d.id === SAMPLE.id)) {
      if (documents.length >= MAX_DOCUMENTS) { setError('Remove a document before adding the sample.'); return; }
      uploadLock.current = true;
      setProcessing('Reading the sample PDF…');
      try {
        const response = await fetch('/sample.pdf');
        if (!response.ok) throw new Error('The sample PDF could not be loaded. Please try uploading a PDF.');
        const doc = await readPdf(new File([await response.blob()], SAMPLE.name, { type: 'application/pdf' }));
        setDocuments(previous => [...previous, { ...doc, id: SAMPLE.id, sample: true }]);
      } catch (error) {
        setError(error instanceof Error ? error.message : 'Could not open the sample PDF.');
        return;
      } finally { setProcessing(''); uploadLock.current = false; }
    }
    setError('');
  }

  async function ask(value = question) {
    if (busy || processing || !value.trim() || !passages.length) return;
    setBusy(true); setError(''); setQuestion('');
    const sources = retrieve(value, passages);
    const controller = new AbortController();
    request.current = controller;
    try {
      const response: Answer = extractiveAnswer(sources);
      setMessages(previous => [...previous, { id: crypto.randomUUID(), question: value, response }]);
      setSelected(response.sources[0] ?? null);
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return;
      setError(error instanceof Error ? error.message : 'Could not connect. Please try again.'); setQuestion(value);
    } finally { setBusy(false); request.current = null; }
  }

  function reset() {
    request.current?.abort(); setMessages([]); setDocuments([]); setSelected(null); setQuestion(''); setError('');
  }
  function downloadChat() {
    const text = messages.map(m => `QUESTION: ${m.question}\n\n${m.response.answer}\n\nSOURCES\n${m.response.sources.map((p, i) => `[${i + 1}] ${p.source}, page ${p.page}\n${p.text}`).join('\n\n')}`).join('\n\n---\n\n');
    const url = URL.createObjectURL(new Blob([text], { type: 'text/plain;charset=utf-8' }));
    const a = document.createElement('a'); a.href = url; a.download = 'jebickson-ai-conversation.txt'; a.click(); URL.revokeObjectURL(url);
  }

  return <div className={`app-shell ${sidebar ? '' : 'sidebar-hidden'}`}>
    {sidebar && <button className="mobile-backdrop" aria-label="Dismiss sources drawer" onClick={() => setSidebar(false)}/>}
    <aside className="sidebar" aria-label="Documents sidebar" inert={help}>
      <button className="icon-button mobile-close" aria-label="Close sources" onClick={() => setSidebar(false)}><X size={20}/></button>
      <a className="brand" href="/" aria-label="Jebickson AI home"><span className="brand-icon"><BookOpen size={22}/></span><span>Jebickson<span className="ai-badge">AI</span></span></a>
      <button className="new-session" onClick={reset} disabled={!!processing || busy}><Plus size={18}/> New notebook</button>
      <div className="section-label"><span>YOUR DOCUMENTS</span><span className="count">{documents.length}</span></div>
      <div className={`upload-zone ${dragging ? 'dragging' : ''}`} onDragOver={e => { e.preventDefault(); setDragging(true); }} onDragLeave={() => setDragging(false)} onDrop={e => { e.preventDefault(); setDragging(false); void upload(e.dataTransfer.files); }}>
        <button disabled={!!processing || busy} onClick={() => fileInput.current?.click()}>
          {processing ? <LoaderCircle className="spin" size={25}/> : <Upload size={25}/>}
          <strong>{processing ? 'Reading document…' : 'Drop your PDFs here'}</strong><span>or click to browse</span><small>Up to 15 MB · 100 pages per PDF</small>
        </button>
      </div>
      <input ref={fileInput} type="file" accept="application/pdf,.pdf" multiple hidden aria-label="Upload PDF documents" onChange={e => void upload(e.target.files)}/>
      <div className="document-list">
        {!documents.length && <div className="empty-docs"><FileText size={25}/><p>A little context goes a long way.</p><span>Your documents will appear here.</span></div>}
        {documents.map(doc => <div className="document" key={doc.id}>
          <FileText size={20}/><button className="document-title" onClick={() => setSelected(doc.passages[0])}><strong>{doc.name}</strong><span>{doc.pages} pages {doc.sample ? '· Sample guide' : '· Ready to explore'}</span></button>
          <button className="icon-button" disabled={busy || !!processing} aria-label={`Remove ${doc.name}`} onClick={() => { setDocuments(previous => previous.filter(d => d.id !== doc.id)); setMessages([]); setSelected(null); }}><X size={15}/></button>
        </div>)}
      </div>
      <div className="sidebar-bottom">
        <div className="privacy-note"><ShieldCheck size={19}/><div><strong>Your files stay with you</strong><p>PDFs are read and searched in your browser. No document uploads.</p></div></div>
        <button className="help-button" onClick={() => setHelp(true)}><CircleHelp size={17}/> How it works & privacy</button>
        <a className="creator" href="https://github.com/jebickson/DocuMind-AI" target="_blank" rel="noreferrer"><span className="avatar">J</span><span><strong>Built by Jebickson</strong><small>View the project on GitHub</small></span><CodeXml size={17}/></a>
      </div>
    </aside>

    <main className="main" inert={help}>
      <header className="topbar"><div><button className="icon-button sidebar-toggle" onClick={() => setSidebar(!sidebar)} aria-label={sidebar ? 'Hide document sidebar' : 'Show document sidebar'}>{sidebar ? <PanelLeftClose size={20}/> : <PanelLeftOpen size={20}/>}<span className="mobile-source-label">Sources ({documents.length})</span></button><span className="breadcrumb">Your notebook <span>/</span> <strong>Reading room</strong></span></div><span className="workspace-badge"><ShieldCheck size={14}/> Free & private</span></header>
      <div className="workspace-header"><div><div className="eyebrow">THE READER’S NOTEBOOK · JEBICKSON AI</div><h1>A notebook for<br/><span>curious minds.</span></h1><p>Your PDFs, their words. Find the passage you’re looking for.</p></div><div className="heading-icon"><Sparkles size={30}/></div></div>

      <div className={`workspace ${selected ? 'with-evidence' : ''}`}>
        <section className="chat-panel" aria-label="Document chat">
          <div className="panel-header"><span><MessageSquare size={18}/> Ask your documents</span><div className="chat-actions">{messages.length > 0 && <><button className="icon-button" onClick={downloadChat} aria-label="Download conversation"><Download size={17}/></button><button className="icon-button" disabled={busy} onClick={() => { setMessages([]); setSelected(null); }} aria-label="Clear conversation"><Trash2 size={17}/></button></>}<span className="subtle-tag">{documents.length ? `${documents.length} document${documents.length > 1 ? 's' : ''}` : 'New conversation'}</span></div></div>
          <div className={`chat-body ${messages.length ? 'has-messages' : ''}`}>
            {!messages.length && <div className="welcome"><div className="welcome-icon"><Sparkles size={30}/></div><h2>{documents.length ? 'What would you like to discover?' : 'Big documents. Clear evidence.'}</h2><p>{documents.length ? 'Ask a focused question to find matching passages. This free edition quotes your documents without generating AI answers.' : 'Explore your PDFs with private, browser-based search. Find matching excerpts and follow them back to the page.'}</p>
              {!documents.length ? <><button className="primary-button" onClick={() => fileInput.current?.click()} disabled={!!processing}><Plus size={17}/> Add your first PDF</button><button className="sample-button" onClick={sample}><BookOpen size={16}/> Just exploring? Try a sample document</button></> : <div className="suggestions">{(documents.some(d => d.sample) ? suggestions : ['Summarize the key points', 'Give me an overview']).map(q => <button key={q} disabled={busy} onClick={() => void ask(q)}><Sparkles size={15}/>{q}</button>)}</div>}
              <div className="feature-row"><div><Search size={18}/><span>Find what matters</span></div><div><Quote size={18}/><span>Follow every source</span></div><div><Layers size={18}/><span>Connect your PDFs</span></div></div>
            </div>}
            {messages.map(message => <article className="exchange" key={message.id}>
              <div className="question"><span className="user-avatar">You</span><p>{message.question}</p></div>
              <div className="answer"><span className="answer-icon"><Sparkles size={17}/></span><div className="answer-content"><div className="answer-label">Jebickson AI <span>{message.response.mode === 'ai' ? 'AI answer' : 'Document excerpts'}</span></div>{message.response.notice && <p className="notice">{message.response.notice}</p>}<div className="answer-text">{message.response.answer}</div><div className="source-buttons">{message.response.sources.map((p, i) => <button key={p.id} onClick={() => setSelected(p)}><span>{i + 1}</span>{p.source}<small>p. {p.page}</small></button>)}</div>{message.response.mode === 'ai' && <small className="answer-disclaimer">Check the source passages. AI can make mistakes.</small>}</div></div>
            </article>)}
            {busy && <div className="thinking" role="status"><LoaderCircle className="spin" size={18}/> Reading between the lines… <button onClick={() => request.current?.abort()}>Cancel</button></div>}
            <div ref={end}/>
          </div>
          <div className="composer-area">{error && <div className="error" role="alert">{error}<button className="icon-button" onClick={() => setError('')} aria-label="Dismiss error"><X size={16}/></button></div>}{processing && <p className="processing" role="status">{processing}</p>}
            <form className="composer" onSubmit={e => { e.preventDefault(); void ask(); }}><label className="sr-only" htmlFor="question">Ask a question about your PDFs</label><textarea id="question" rows={2} maxLength={1200} placeholder={documents.length ? 'Search your documents with a question…' : 'Add a document to start the conversation…'} value={question} disabled={busy || !!processing || !documents.length} onChange={e => setQuestion(e.target.value)} onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); void ask(); } }}/><div className="composer-bottom"><span className="mode-toggle"><ShieldCheck size={14}/> Free excerpt search <span>· stays in this browser</span></span><button className="send-button" disabled={busy || !!processing || !question.trim() || !documents.length} aria-label="Send question"><Send size={17}/></button></div></form>
            <p className="composer-note">Answers grounded in your documents. Always follow the source.</p>
          </div>
        </section>

        {selected && <aside className="evidence-panel" aria-label="Source evidence"><div className="panel-header"><span><Quote size={17}/> Source passage</span><button className="icon-button" aria-label="Close source passage" onClick={() => setSelected(null)}><X size={17}/></button></div><div className="evidence-body"><span className="evidence-label">BACK TO THE ORIGINAL</span><h3>{selected.source}</h3><span className="page-pill"><FileText size={14}/> Page {selected.page}</span><blockquote>{selected.text}</blockquote><div className="evidence-footer"><Check size={16}/> Extracted from the source text</div></div></aside>}
      </div>
      <footer className="main-footer"><span>Less searching. More understanding.</span><span>Jebickson AI <span className="footer-dot">·</span> An independent project</span></footer>
    </main>

    {help && <div className="modal-backdrop" onClick={() => setHelp(false)}><section className="modal" role="dialog" aria-modal="true" aria-labelledby="help-title" onClick={e => e.stopPropagation()}><button autoFocus className="icon-button modal-close" onClick={() => setHelp(false)} aria-label="Close help"><X size={20}/></button><BookOpen className="purple" size={28}/><h2 id="help-title">A clearer way to read</h2><p>Add up to five text-based PDFs. Jebickson AI extracts the text locally and searches for passages matching your question. This free public edition returns original excerpts, not AI-generated answers.</p><h3>Your documents and privacy</h3><p>PDF files, questions, and conversations stay in this browser tab and disappear on refresh. No document text is sent to a server or AI provider. Download a conversation if you want to keep it.</p><h3>Know the limits</h3><p>Search uses keyword ranking. It may miss synonyms. Scanned or image-only PDFs need OCR first. Overview requests show selected passages, not a full summary. Source page numbers use the PDF’s page order, which may differ from printed page numbers.</p><button className="primary-button" onClick={() => setHelp(false)}>Got it</button></section></div>}
  </div>;
}
