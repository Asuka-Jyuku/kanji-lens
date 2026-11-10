import type { Drawing } from '../../domain/drawing';
import { RecognitionRequest, toRecognitionRequest } from '../../domain/recognition-request';
import type { StrokeOrderMode } from '../../domain/stroke-order-mode';

/**
 * A drawing saved as a test sample (#66): the API body, unchanged, next to the answer key the
 * person who drew it fills in. The API rejects unknown fields, so the key sits beside the
 * request, never inside it. The format is described in docs/MODEL.md, "Desenhos do canvas".
 */
export const DRAWING_SAMPLE_FORMAT = 'kanjilens-drawing';
export const DRAWING_SAMPLE_VERSION = 1;

/**
 * The stroke order used on purpose: right, or which mistake. The mistakes are the ADR 0016
 * issue types (`order`, `direction`, `joined`, `broken`), plus a stroke too many or too few,
 * which the API answers as `stroke_count_mismatch` when the difference is over 2.
 */
export const STROKE_ORDER_LABELS = [
  'correct',
  'order',
  'direction',
  'joined',
  'broken',
  'extra',
  'missing',
] as const;

export type StrokeOrderLabel = (typeof STROKE_ORDER_LABELS)[number];

export function isStrokeOrderLabel(value: unknown): value is StrokeOrderLabel {
  return (STROKE_ORDER_LABELS as readonly unknown[]).includes(value);
}

/** The answer key of a sample. */
export interface DrawingLabel {
  /** The kanji meant, one character. */
  readonly kanji: string;
  readonly stroke_order: StrokeOrderLabel;
  /** The drawn strokes the mistake is on, from 1, as the API numbers them; empty when right. */
  readonly strokes: readonly number[];
}

export interface DrawingSample {
  readonly format: typeof DRAWING_SAMPLE_FORMAT;
  readonly version: typeof DRAWING_SAMPLE_VERSION;
  /** When it was saved, in UTC (ISO 8601). */
  readonly exported_at: string;
  readonly label: DrawingLabel;
  readonly request: RecognitionRequest;
}

/** Exactly one Han character (a kanji), as the key of a sample. */
export function isSingleKanji(text: string): boolean {
  return /^\p{Script=Han}$/u.test(text);
}

/**
 * The stroke numbers typed as "3, 4" (commas or spaces), sorted and without repeats; `null`
 * when one is not a whole number between 1 and the strokes drawn. Empty text is no strokes.
 */
export function parseStrokeNumbers(text: string, strokeCount: number): readonly number[] | null {
  const parts = text.split(/[\s,]+/).filter((part) => part !== '');
  const numbers = new Set<number>();
  for (const part of parts) {
    if (!/^\d+$/.test(part)) {
      return null;
    }
    const value = Number(part);
    if (value < 1 || value > strokeCount) {
      return null;
    }
    numbers.add(value);
  }
  return [...numbers].sort((a, b) => a - b);
}

export function drawingSample(
  drawing: Drawing,
  mode: StrokeOrderMode,
  label: DrawingLabel,
  exportedAt: Date,
): DrawingSample {
  return {
    format: DRAWING_SAMPLE_FORMAT,
    version: DRAWING_SAMPLE_VERSION,
    exported_at: exportedAt.toISOString(),
    // A right order has no stroke to point at.
    label: { ...label, strokes: label.stroke_order === 'correct' ? [] : [...label.strokes] },
    request: toRecognitionRequest(drawing, mode),
  };
}

/**
 * The file content: indented JSON with each list of numbers (a point `[x, y, t]`, the stroke
 * numbers) on one line, so a drawing reads and diffs one point per line.
 */
export function serializeSample(sample: DrawingSample): string {
  const number = String.raw`-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?`;
  const numberList = new RegExp(String.raw`\[\s*(${number}(?:,\s*${number})*)\s*\]`, 'g');
  const json = JSON.stringify(sample, null, 2).replace(
    numberList,
    (_, items: string) => `[${items.split(/,\s*/).join(', ')}]`,
  );
  return `${json}\n`;
}

/**
 * An ASCII file name that sorts by kanji, then mistake, then time:
 * `u65e5-order-20261110T153045Z.json` for 日 drawn out of order.
 */
export function sampleFileName(sample: DrawingSample): string {
  const codePoint = sample.label.kanji.codePointAt(0)?.toString(16) ?? 'unknown';
  const time = sample.exported_at.replace(/\.\d+/, '').replace(/[-:]/g, '');
  return `u${codePoint}-${sample.label.stroke_order}-${time}.json`;
}
