import type { DrawingSample } from '../drawing-export/drawing-sample';
import {
  DEFAULT_COLLECTION_KANJI,
  batchFileName,
  collectionQueue,
  drawingBatch,
  isWriterCode,
  parseKanjiList,
} from './collection-batch';

/** A repeatable stand-in for Math.random. */
function seeded(seed: number): () => number {
  let state = seed;
  return () => {
    state = (state * 1103515245 + 12345) % 2147483648;
    return state / 2147483648;
  };
}

function count(queue: readonly string[]): Map<string, number> {
  const counts = new Map<string, number>();
  for (const kanji of queue) {
    counts.set(kanji, (counts.get(kanji) ?? 0) + 1);
  }
  return counts;
}

describe('collection batch', () => {
  it('starts with the 40 first classes of the real set, all different kanji', () => {
    expect(parseKanjiList(DEFAULT_COLLECTION_KANJI)).toHaveLength(40);
  });

  it('accepts a code for who draws, and nothing that is a name or leaves a folder', () => {
    expect(isWriterCode('a')).toBe(true);
    expect(isWriterCode('p2')).toBe(true);
    expect(isWriterCode('team-b')).toBe(true);
    expect(isWriterCode('')).toBe(false);
    expect(isWriterCode('Ana')).toBe(false);
    expect(isWriterCode('a b')).toBe(false);
    expect(isWriterCode('../a')).toBe(false);
    expect(isWriterCode('-a')).toBe(false);
    expect(isWriterCode('a'.repeat(17))).toBe(false);
  });

  it('reads the kanji in order, without repeats, ignoring spaces and commas', () => {
    expect(parseKanjiList(' 日 目、日,\n白 ')).toEqual(['日', '目', '白']);
  });

  it('refuses a list with anything but kanji, or none', () => {
    expect(parseKanjiList('日 a')).toBeNull();
    expect(parseKanjiList('日に')).toBeNull();
    expect(parseKanjiList(' , ')).toBeNull();
  });

  it('asks for every kanji the number of times chosen, a round at a time', () => {
    const kanji = ['日', '目', '白', '百'];
    const queue = collectionQueue(kanji, 3, seeded(7));

    expect(queue).toHaveLength(12);
    expect([...count(queue).values()]).toEqual([3, 3, 3, 3]);
    for (let round = 0; round < 3; round++) {
      expect(new Set(queue.slice(round * 4, round * 4 + 4))).toEqual(new Set(kanji));
    }
  });

  it('never asks for the same kanji twice in a row', () => {
    for (let seed = 1; seed <= 200; seed++) {
      const queue = collectionQueue(['日', '目'], 5, seeded(seed));
      expect(queue.every((kanji, i) => i === 0 || kanji !== queue[i - 1])).toBe(true);
    }
  });

  it('wraps the drawings with who drew them, and names the file by person and time', () => {
    const sample = { format: 'kanjilens-drawing' } as unknown as DrawingSample;
    const batch = drawingBatch('p2', [sample], new Date(Date.UTC(2026, 10, 13, 15, 30, 45, 9)));

    expect(batch).toEqual({
      format: 'kanjilens-drawing-batch',
      version: 1,
      exported_at: '2026-11-13T15:30:45.009Z',
      writer: 'p2',
      samples: [sample],
    });
    expect(batchFileName(batch)).toBe('batch-p2-20261113T153045Z.json');
  });
});
