import { MAX_CHARACTERS, MAX_PAGES, splitPage, type DocumentInfo } from './documents';

export async function readPdf(file: File): Promise<DocumentInfo> {
  if (!file.name.toLowerCase().endsWith('.pdf')) throw new Error('Please choose a PDF file.');
  if (file.size > 15 * 1024 * 1024) throw new Error(`${file.name}: the maximum file size is 15 MB.`);
  const pdfjs = await import('pdfjs-dist');
  pdfjs.GlobalWorkerOptions.workerSrc = '/pdfjs/pdf.worker.min.mjs';
  const task = pdfjs.getDocument({ data: new Uint8Array(await file.arrayBuffer()), cMapUrl: '/pdfjs/cmaps/', cMapPacked: true, standardFontDataUrl: '/pdfjs/standard_fonts/', wasmUrl: '/pdfjs/wasm/' });
  try {
    const pdf = await task.promise;
    if (pdf.numPages > MAX_PAGES) throw new Error(`${file.name}: please use a PDF with ${MAX_PAGES} pages or fewer.`);
    const id = crypto.randomUUID();
    const passages: DocumentInfo['passages'] = [];
    let characters = 0;
    for (let page = 1; page <= pdf.numPages; page++) {
      const content = await (await pdf.getPage(page)).getTextContent();
      const text = content.items.map(item => 'str' in item ? item.str : '').join(' ');
      characters += text.length;
      if (characters > MAX_CHARACTERS) throw new Error(`${file.name}: too much text. Split this PDF into smaller documents.`);
      passages.push(...splitPage(text, file.name.slice(0, 180), page, id));
    }
    if (!passages.length) throw new Error(`${file.name}: no readable text found. Scanned PDFs need OCR first.`);
    return { id, name: file.name.slice(0, 180), pages: pdf.numPages, passages };
  } catch (error) {
    if (error instanceof Error && error.name === 'PasswordException') throw new Error('This PDF is password-protected. Upload an unlocked copy.');
    throw error;
  } finally { await task.destroy(); }
}
