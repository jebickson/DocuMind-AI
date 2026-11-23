import { test } from 'node:test';
import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { getDocument } from 'pdfjs-dist/legacy/build/pdf.mjs';

test('real sample PDF extracts all pages and keeps evidence on page 2', async () => {
  const task = getDocument({ data: new Uint8Array(await readFile('public/sample.pdf')), useSystemFonts: true });
  try {
    const pdf = await task.promise;
    assert.equal(pdf.numPages, 3);
    const page = await pdf.getPage(2);
    const text = (await page.getTextContent()).items.map(item => 'str' in item ? item.str : '').join(' ');
    assert.match(text, /six stages/);
    assert.match(text, /Return citations/);
  } finally { await task.destroy(); }
});

test('invalid PDF data rejects instead of accepting arbitrary bytes', async () => {
  const task = getDocument({ data: new TextEncoder().encode('This is not a PDF') });
  try { await assert.rejects(task.promise); }
  finally { await task.destroy(); }
});
