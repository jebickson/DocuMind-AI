import { test } from 'node:test';
import assert from 'node:assert/strict';
import { splitPage, retrieve, extractiveAnswer, SAMPLE } from '../lib/documents.ts';

test('chunks preserve source and page metadata with bounded overlap', () => {
  const chunks = splitPage('alpha beta gamma '.repeat(250), 'example.pdf', 7, 'doc');
  assert.ok(chunks.length > 1);
  assert.ok(chunks.every(p => p.page === 7 && p.source === 'example.pdf' && p.text.length <= 1500));
  assert.equal(chunks[0].text.slice(-180), chunks[1].text.slice(0, 180));
  assert.equal(new Set(chunks.map(p => p.id)).size, chunks.length);
});
test('empty pages do not create passages', () => assert.deepEqual(splitPage('  \n ', 'empty.pdf', 1, 'doc'), []));
test('retrieval ranks the specific evidence and keeps page references', () => {
  const results = retrieve('What are the six stages of RAG?', SAMPLE.passages);
  assert.equal(results[0].page, 2);
});
test('unrelated questions return no fabricated answer', () => {
  const result = extractiveAnswer(retrieve('What is the price of Bitcoin?', SAMPLE.passages));
  assert.equal(result.sources.length, 0);
  assert.match(result.answer, /could not find/);
});
test('broad overview samples across document rather than one starting page', () => {
  const results = retrieve('Summarize the key points', SAMPLE.passages);
  assert.equal(results.length, 3);
  assert.equal(results[2].page, 3);
  assert.equal(retrieve('Show an overview', SAMPLE.passages).length, 3);
});
test('citations map to exact original passages, including same page in different PDFs', () => {
  const sources = [{ id: 'a', source: 'a.pdf', page: 1, text: 'alpha evidence' }, { id: 'b', source: 'b.pdf', page: 1, text: 'beta evidence' }];
  const result = extractiveAnswer(sources);
  assert.equal(result.mode, 'extractive');
  assert.ok(result.answer.includes('alpha evidence [1]'));
  assert.ok(result.answer.includes('beta evidence [2]'));
  assert.deepEqual(result.sources, sources);
});
test('Unicode words can retrieve matching evidence', () => {
  const sources = [{ id: 'a', source: 'guide.pdf', page: 1, text: 'தமிழ் மொழி உலகம்' }];
  assert.equal(retrieve('தமிழ்', sources).length, 1);
});
