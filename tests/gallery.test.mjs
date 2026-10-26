import test from 'node:test';
import assert from 'node:assert/strict';
import { filterSkills, formatDuration, safeUrl } from '../site/app.mjs';

const skills = [
  { id: 'recast', title: 'MV recast', description: 'Depth character replacement', category: 'Music video', styles: ['Anime', 'Cinematic'], examples: [{ title: 'Dance sequence', description: 'Full choreography' }] },
  { id: 'product', title: 'Product film', description: 'A studio product workflow', category: 'Advertising', styles: ['Cinematic'], examples: [] },
];

test('category and style intersect without making duplicate skills', () => {
  assert.deepEqual(filterSkills(skills, { category: 'Music video', style: 'Cinematic' }).map(s => s.id), ['recast']);
  assert.deepEqual(filterSkills(skills, { category: 'Advertising', style: 'Anime' }), []);
  assert.equal(filterSkills(skills, { style: 'Cinematic' }).length, 2);
});

test('search includes example and technique text and combines with filters', () => {
  assert.deepEqual(filterSkills(skills, { query: '  DEPTH dance ' }).map(s => s.id), ['recast']);
  assert.deepEqual(filterSkills(skills, { query: 'dance', category: 'Advertising' }), []);
  assert.equal(filterSkills(skills, { query: ' ' }).length, 2);
});

test('duration rounds consistently across minute boundary', () => {
  assert.equal(formatDuration(132.54), '2:13');
  assert.equal(formatDuration(59.6), '1:00');
});

test('links resolve within project subpath and reject executable schemes', () => {
  assert.equal(safeUrl('media/film.mp4', 'https://example.org/skills/'), 'https://example.org/skills/media/film.mp4');
  assert.throws(() => safeUrl('javascript:alert(1)', 'https://example.org/'));
  assert.throws(() => safeUrl('data:text/html,hi', 'https://example.org/'));
});
