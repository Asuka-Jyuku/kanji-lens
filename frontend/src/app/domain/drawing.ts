/**
 * The drawing as the canvas captures it: strokes of [x, y, t] points, as drawn (ADR 0016).
 *
 * x and y are CSS pixels from the canvas top-left corner; t is milliseconds since the first
 * point of the drawing, a whole number that never goes back. Nothing here smooths, resamples or
 * normalizes the points: that is preprocessing and lives only in kanjilens_ml (CLAUDE.md,
 * "Pré-processamento sempre junto"). Every function is pure and returns a new value.
 */

export interface Point {
  readonly x: number;
  readonly y: number;
  readonly t: number;
}

export type Stroke = readonly Point[];

export interface CanvasSize {
  readonly width: number;
  readonly height: number;
}

export interface Drawing {
  readonly canvas: CanvasSize;
  readonly strokes: readonly Stroke[];
}

/** The same limits the API enforces (ADR 0016; backend domain/drawing.py). */
export const DRAWING_LIMITS = {
  maxStrokes: 40,
  maxPointsPerStroke: 1_000,
  maxTotalPoints: 10_000,
  /** Fraction of each side a point may fall outside the canvas. */
  canvasMargin: 0.1,
} as const;

/** Why a point was not added; the screen turns it into a message (ADR 0009). */
export type DrawingLimit = 'max_strokes' | 'max_points_per_stroke' | 'max_total_points';

/**
 * The drawing being captured, plus what capturing needs and the API does not: the time of the
 * first point (to count t from it) and whether a stroke is open.
 */
export interface DrawingCapture {
  readonly drawing: Drawing;
  /** Event time (ms, any clock) of the first point of the drawing; null while it is empty. */
  readonly origin: number | null;
  readonly strokeOpen: boolean;
}

export interface CaptureUpdate {
  readonly capture: DrawingCapture;
  /** Set when the point was refused because a limit was reached. */
  readonly limit?: DrawingLimit;
}

/** A pointer position in CSS pixels from the canvas corner, with the event time in ms. */
export interface PointerSample {
  readonly x: number;
  readonly y: number;
  readonly time: number;
}

export function emptyCapture(canvas: CanvasSize): DrawingCapture {
  return { drawing: { canvas, strokes: [] }, origin: null, strokeOpen: false };
}

export function pointCount(drawing: Drawing): number {
  return drawing.strokes.reduce((total, stroke) => total + stroke.length, 0);
}

export function isEmpty(drawing: Drawing): boolean {
  return drawing.strokes.length === 0;
}

/** Opens a new stroke at the sample, unless the drawing already has the most strokes allowed. */
export function startStroke(capture: DrawingCapture, sample: PointerSample): CaptureUpdate {
  const { drawing } = capture;
  if (drawing.strokes.length >= DRAWING_LIMITS.maxStrokes) {
    return { capture: { ...capture, strokeOpen: false }, limit: 'max_strokes' };
  }
  if (pointCount(drawing) >= DRAWING_LIMITS.maxTotalPoints) {
    return { capture: { ...capture, strokeOpen: false }, limit: 'max_total_points' };
  }
  const origin = capture.origin ?? sample.time;
  const point = toPoint(sample, drawing, origin);
  return {
    capture: {
      drawing: { ...drawing, strokes: [...drawing.strokes, [point]] },
      origin,
      strokeOpen: true,
    },
  };
}

/** Adds the sample to the open stroke; does nothing when no stroke is open. */
export function extendStroke(capture: DrawingCapture, sample: PointerSample): CaptureUpdate {
  const { drawing, origin } = capture;
  if (!capture.strokeOpen || origin === null || isEmpty(drawing)) {
    return { capture };
  }
  const last = drawing.strokes[drawing.strokes.length - 1];
  if (last.length >= DRAWING_LIMITS.maxPointsPerStroke) {
    return { capture, limit: 'max_points_per_stroke' };
  }
  if (pointCount(drawing) >= DRAWING_LIMITS.maxTotalPoints) {
    return { capture, limit: 'max_total_points' };
  }
  const point = toPoint(sample, drawing, origin);
  const strokes = [...drawing.strokes.slice(0, -1), [...last, point]];
  return { capture: { ...capture, drawing: { ...drawing, strokes } } };
}

export function endStroke(capture: DrawingCapture): DrawingCapture {
  return capture.strokeOpen ? { ...capture, strokeOpen: false } : capture;
}

/** Removes the last stroke; an emptied drawing counts t from its next first point again. */
export function undoLastStroke(capture: DrawingCapture): DrawingCapture {
  const strokes = capture.drawing.strokes.slice(0, -1);
  return {
    drawing: { ...capture.drawing, strokes },
    origin: strokes.length === 0 ? null : capture.origin,
    strokeOpen: false,
  };
}

export function clearDrawing(capture: DrawingCapture): DrawingCapture {
  return emptyCapture(capture.drawing.canvas);
}

/**
 * The canvas changed size (the phone turned, the window resized): the strokes scale with it,
 * so the drawing keeps its shape and its points stay in the canvas the API is told about.
 * The time of each point does not change.
 */
export function resizeCanvas(capture: DrawingCapture, canvas: CanvasSize): DrawingCapture {
  const { drawing } = capture;
  if (canvas.width === drawing.canvas.width && canvas.height === drawing.canvas.height) {
    return capture;
  }
  const scaleX = drawing.canvas.width > 0 ? canvas.width / drawing.canvas.width : 1;
  const scaleY = drawing.canvas.height > 0 ? canvas.height / drawing.canvas.height : 1;
  const strokes = drawing.strokes.map((stroke) =>
    stroke.map((point) => ({ x: point.x * scaleX, y: point.y * scaleY, t: point.t })),
  );
  return { ...capture, drawing: { canvas, strokes } };
}

function toPoint(sample: PointerSample, drawing: Drawing, origin: number): Point {
  const { width, height } = drawing.canvas;
  const marginX = width * DRAWING_LIMITS.canvasMargin;
  const marginY = height * DRAWING_LIMITS.canvasMargin;
  // Pointer capture keeps a stroke going when the finger leaves the canvas; points far outside
  // would make the API refuse the whole drawing, so they stop at the margin it accepts.
  const x = clamp(sample.x, -marginX, width + marginX);
  const y = clamp(sample.y, -marginY, height + marginY);
  // Coalesced and touch events may arrive with equal or slightly older times: t never goes back.
  const previous = lastPoint(drawing)?.t ?? 0;
  const t = Math.max(previous, Math.round(sample.time - origin));
  return { x, y, t };
}

function lastPoint(drawing: Drawing): Point | undefined {
  const last = drawing.strokes[drawing.strokes.length - 1];
  return last?.[last.length - 1];
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(Math.max(value, min), max);
}
