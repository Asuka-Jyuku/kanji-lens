import type { CanvasSize, Drawing } from './drawing';
import type { StrokeOrderMode } from './stroke-order-mode';

/**
 * The body of POST /api/recognitions, field for field (ARCHITECTURE.md, section 2.2; ADR 0016):
 * the mode, the canvas size and the strokes as [x, y, t], exactly as drawn. The names follow
 * the API, not TypeScript, because this is the wire format; the drawing export (#66) writes the
 * same object.
 */
export interface RecognitionRequest {
  readonly stroke_order_mode: StrokeOrderMode;
  readonly canvas: CanvasSize;
  readonly strokes: [number, number, number][][];
}

/** The drawing and the mode as the API takes them; nothing is smoothed or resampled. */
export function toRecognitionRequest(drawing: Drawing, mode: StrokeOrderMode): RecognitionRequest {
  return {
    stroke_order_mode: mode,
    canvas: { width: drawing.canvas.width, height: drawing.canvas.height },
    strokes: drawing.strokes.map((stroke) => stroke.map(({ x, y, t }) => [x, y, t])),
  };
}
