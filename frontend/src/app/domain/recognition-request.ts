import type { Drawing } from './drawing';
import type { StrokeOrderMode } from './stroke-order-mode';

/**
 * The body of `POST /api/recognitions` (ARCHITECTURE.md, section 2.2; ADR 0016): the mode and
 * the strokes as drawn, each point as `[x, y, t]`. The names are the API's, in snake_case.
 */
export interface RecognitionRequest {
  stroke_order_mode: StrokeOrderMode;
  canvas: { width: number; height: number };
  strokes: [number, number, number][][];
}

/** The drawing and the chosen mode as the API takes them, with nothing added or changed. */
export function toRecognitionRequest(drawing: Drawing, mode: StrokeOrderMode): RecognitionRequest {
  return {
    stroke_order_mode: mode,
    canvas: { width: drawing.canvas.width, height: drawing.canvas.height },
    strokes: drawing.strokes.map((stroke) => stroke.map(({ x, y, t }) => [x, y, t])),
  };
}
