import type { DrawingSample } from '../drawing-export/drawing-sample';

/**
 * The collection session (#100): the team draws the real recognition set (#93) one kanji after
 * another, and downloads the drawings as one batch. `ml/scripts/import_drawings.py` splits the
 * batch into one file per drawing, in the format of the drawing export (#66). Both formats are
 * described in docs/MODEL.md, "Desenhos do canvas".
 */
export const DRAWING_BATCH_FORMAT = 'kanjilens-drawing-batch';
export const DRAWING_BATCH_VERSION = 1;

/**
 * The first 40 classes of the real set (#93), grouped by look-alikes. The list that counts is
 * ml/drawings/recognition/classes.txt: the import script refuses a kanji outside it. This is
 * only what the session starts with, and the person can change it.
 */
export const DEFAULT_COLLECTION_KANJI =
  '日目白百自人入八大太犬天木本休体王玉土工力刀万方午牛貝見右石九丸円内間聞姉妹気汽';
export const DEFAULT_REPETITIONS = 5;
export const MAX_REPETITIONS = 20;

export interface DrawingBatch {
  readonly format: typeof DRAWING_BATCH_FORMAT;
  readonly version: typeof DRAWING_BATCH_VERSION;
  /** When it was downloaded, in UTC (ISO 8601). */
  readonly exported_at: string;
  /** Who drew it, as a code and never a name: the folder of the drawings, for the split by person. */
  readonly writer: string;
  readonly samples: readonly DrawingSample[];
}

/**
 * A code for who draws, such as `a` or `p2`: lowercase ASCII letters, digits and hyphens, up to
 * 16, starting with a letter or digit. It becomes a folder name, so nothing else gets in.
 */
export function isWriterCode(text: string): boolean {
  return /^[a-z0-9][a-z0-9-]{0,15}$/.test(text);
}

/**
 * The kanji typed as a list, in order and without repeats; spaces, commas and line breaks
 * separate nothing and are ignored. `null` when anything else is not a kanji, or the list is
 * empty.
 */
export function parseKanjiList(text: string): readonly string[] | null {
  const characters = [...text.replace(/[\s,、，]+/gu, '')];
  if (characters.length === 0 || !characters.every((each) => /^\p{Script=Han}$/u.test(each))) {
    return null;
  }
  return [...new Set(characters)];
}

/**
 * The order to draw in: `repetitions` rounds, each one every kanji once, shuffled. Rounds mean
 * a session stopped halfway still covers every class about evenly, and copies of a kanji are
 * a round apart, never drawn twice in a row from memory of the last one. `random` returns a
 * number in [0, 1), like `Math.random`.
 */
export function collectionQueue(
  kanji: readonly string[],
  repetitions: number,
  random: () => number,
): readonly string[] {
  const queue: string[] = [];
  for (let round = 0; round < repetitions; round++) {
    const next = shuffled(kanji, random);
    // The round boundary: the first of this round must not repeat the last of the one before.
    if (next.length > 1 && next[0] === queue.at(-1)) {
      [next[0], next[1]] = [next[1], next[0]];
    }
    queue.push(...next);
  }
  return queue;
}

function shuffled(items: readonly string[], random: () => number): string[] {
  const copy = [...items];
  // Fisher–Yates.
  for (let i = copy.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

export function drawingBatch(
  writer: string,
  samples: readonly DrawingSample[],
  exportedAt: Date,
): DrawingBatch {
  return {
    format: DRAWING_BATCH_FORMAT,
    version: DRAWING_BATCH_VERSION,
    exported_at: exportedAt.toISOString(),
    writer,
    samples: [...samples],
  };
}

/** An ASCII file name that sorts by person, then time: `batch-a-20261113T153045Z.json`. */
export function batchFileName(batch: DrawingBatch): string {
  const time = batch.exported_at.replace(/\.\d+/, '').replace(/[-:]/g, '');
  return `batch-${batch.writer}-${time}.json`;
}
