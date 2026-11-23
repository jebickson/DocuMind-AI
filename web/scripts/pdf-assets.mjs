import { mkdir, copyFile, cp, writeFile } from 'node:fs/promises';
import { SAMPLE } from '../lib/documents.ts';
await mkdir('public/pdfjs', { recursive: true });
await copyFile('node_modules/pdfjs-dist/build/pdf.worker.min.mjs', 'public/pdfjs/pdf.worker.min.mjs');
await cp('node_modules/pdfjs-dist/cmaps', 'public/pdfjs/cmaps', { recursive: true });
await cp('node_modules/pdfjs-dist/standard_fonts', 'public/pdfjs/standard_fonts', { recursive: true });
await cp('node_modules/pdfjs-dist/wasm', 'public/pdfjs/wasm', { recursive: true });

// Original demonstration PDF: real PDF parsing is used for both sample and uploads.
const objects = [];
objects.push('<< /Type /Catalog /Pages 2 0 R >>');
objects.push('<< /Type /Pages /Kids [4 0 R 6 0 R 8 0 R] /Count 3 >>');
objects.push('<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>');
for (const passage of SAMPLE.passages) {
  const contentId = objects.length + 2;
  objects.push(`<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents ${contentId} 0 R >>`);
  const words = passage.text.split(' '), lines = [];
  let line = '';
  for (const word of words) { if ((line + ' ' + word).length > 77) { lines.push(line); line = word; } else line += (line ? ' ' : '') + word; }
  if (line) lines.push(line);
  const escape = text => text.replace(/[\\()]/g, '\\$&');
  const stream = `BT /F1 20 Tf 50 730 Td (Jebickson AI - A short guide to RAG) Tj /F1 11 Tf 0 -35 Td ` + lines.map((line, i) => `${i ? '0 -18 Td ' : ''}(${escape(line)}) Tj`).join('\n') + ` 0 -40 Td (Page ${passage.page} - Original demonstration guide by Jebickson) Tj ET`;
  objects.push(`<< /Length ${Buffer.byteLength(stream)} >>\nstream\n${stream}\nendstream`);
}
let pdf = '%PDF-1.4\n';
const offsets = [0];
objects.forEach((object, i) => { offsets.push(Buffer.byteLength(pdf)); pdf += `${i + 1} 0 obj\n${object}\nendobj\n`; });
const xref = Buffer.byteLength(pdf);
pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n` + offsets.slice(1).map(offset => `${String(offset).padStart(10, '0')} 00000 n \n`).join('');
pdf += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`;
await writeFile('public/sample.pdf', pdf);
