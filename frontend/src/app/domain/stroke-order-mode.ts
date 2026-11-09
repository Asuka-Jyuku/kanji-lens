/**
 * Whether the stroke order counts in a recognition (ADR 0012). `ordered` also checks the order
 * and direction of the strokes against KanjiVG; `unordered` only names the kanji. The value is
 * the `stroke_order_mode` the API takes (ARCHITECTURE.md, section 2.2).
 */
export type StrokeOrderMode = 'ordered' | 'unordered';

/** "Não importa" until the user picks otherwise (ADR 0012). */
export const DEFAULT_STROKE_ORDER_MODE: StrokeOrderMode = 'unordered';

/** True for the two modes the API accepts; anything else (a stray form value) is not a mode. */
export function isStrokeOrderMode(value: unknown): value is StrokeOrderMode {
  return value === 'ordered' || value === 'unordered';
}
