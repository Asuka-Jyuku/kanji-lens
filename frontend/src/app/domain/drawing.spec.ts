import {
  CaptureUpdate,
  DRAWING_LIMITS,
  DrawingCapture,
  PointerSample,
  clearDrawing,
  emptyCapture,
  endStroke,
  extendStroke,
  isEmpty,
  pointCount,
  resizeCanvas,
  startStroke,
  undoLastStroke,
} from './drawing';

const CANVAS = { width: 320, height: 320 };
const at = (x: number, y: number, time: number): PointerSample => ({ x, y, time });

/** Draws strokes given as lists of samples, like a pointer would: down, moves, up. */
function draw(strokes: PointerSample[][], start: DrawingCapture = emptyCapture(CANVAS)) {
  let capture = start;
  for (const [first, ...rest] of strokes) {
    capture = startStroke(capture, first).capture;
    for (const sample of rest) {
      capture = extendStroke(capture, sample).capture;
    }
    capture = endStroke(capture);
  }
  return capture;
}

describe('drawing capture', () => {
  it('keeps each stroke as drawn, in order, with t counted from the first point', () => {
    const capture = draw([
      [at(10, 10, 1000), at(20, 30, 1016.4)],
      [at(50, 50, 1400), at(60, 40, 1420), at(70, 30, 1440)],
    ]);

    expect(capture.drawing).toEqual({
      canvas: CANVAS,
      strokes: [
        [
          { x: 10, y: 10, t: 0 },
          { x: 20, y: 30, t: 16 },
        ],
        [
          { x: 50, y: 50, t: 400 },
          { x: 60, y: 40, t: 420 },
          { x: 70, y: 30, t: 440 },
        ],
      ],
    });
  });

  it('never lets t go back, even when events arrive out of time', () => {
    const capture = draw([[at(1, 1, 100), at(2, 2, 150), at(3, 3, 140)]]);

    expect(capture.drawing.strokes[0].map((p) => p.t)).toEqual([0, 50, 50]);
  });

  it('stops points that leave the canvas at the margin the API accepts', () => {
    const margin = CANVAS.width * DRAWING_LIMITS.canvasMargin;
    const capture = draw([[at(160, 160, 0), at(-500, 1000, 10)]]);

    expect(capture.drawing.strokes[0][1]).toEqual({
      x: -margin,
      y: CANVAS.height + margin,
      t: 10,
    });
  });

  it('ignores moves when no stroke is open', () => {
    const capture = extendStroke(emptyCapture(CANVAS), at(5, 5, 0)).capture;

    expect(isEmpty(capture.drawing)).toBe(true);
  });

  it('undoes the last stroke, and an emptied drawing counts t from zero again', () => {
    const two = draw([[at(1, 1, 100)], [at(2, 2, 300)]]);
    const one = undoLastStroke(two);
    const none = undoLastStroke(one);
    const again = draw([[at(5, 5, 900)]], none);

    expect(one.drawing.strokes).toEqual([[{ x: 1, y: 1, t: 0 }]]);
    expect(isEmpty(none.drawing)).toBe(true);
    expect(again.drawing.strokes).toEqual([[{ x: 5, y: 5, t: 0 }]]);
  });

  it('clears everything but the canvas size', () => {
    const cleared = clearDrawing(draw([[at(1, 1, 0), at(2, 2, 5)]]));

    expect(cleared).toEqual(emptyCapture(CANVAS));
  });

  it('scales the strokes with the canvas, keeping the times', () => {
    const capture = draw([[at(100, 50, 0), at(200, 300, 20)]]);

    const resized = resizeCanvas(capture, { width: 160, height: 160 });

    expect(resized.drawing).toEqual({
      canvas: { width: 160, height: 160 },
      strokes: [
        [
          { x: 50, y: 25, t: 0 },
          { x: 100, y: 150, t: 20 },
        ],
      ],
    });
  });

  describe('limits (the same as the API)', () => {
    it('refuses a stroke beyond the most strokes', () => {
      const full = draw(Array.from({ length: DRAWING_LIMITS.maxStrokes }, (_, i) => [at(i, i, i)]));

      const update: CaptureUpdate = startStroke(full, at(1, 1, 999));

      expect(update.limit).toBe('max_strokes');
      expect(update.capture.drawing.strokes).toHaveLength(DRAWING_LIMITS.maxStrokes);
    });

    it('stops a stroke at the most points per stroke', () => {
      let capture = startStroke(emptyCapture(CANVAS), at(0, 0, 0)).capture;
      for (let i = 1; i < DRAWING_LIMITS.maxPointsPerStroke; i++) {
        capture = extendStroke(capture, at(i % 300, 0, i)).capture;
      }

      const update = extendStroke(capture, at(1, 1, 5000));

      expect(update.limit).toBe('max_points_per_stroke');
      expect(update.capture.drawing.strokes[0]).toHaveLength(DRAWING_LIMITS.maxPointsPerStroke);
    });

    it('stops the drawing at the most points in total', () => {
      const perStroke = DRAWING_LIMITS.maxTotalPoints / 10;
      const stroke = (s: number) =>
        Array.from({ length: perStroke }, (_, i) => at(i % 300, s, s * perStroke + i));
      const full = draw(Array.from({ length: 10 }, (_, s) => stroke(s)));

      expect(pointCount(full.drawing)).toBe(DRAWING_LIMITS.maxTotalPoints);
      expect(startStroke(full, at(1, 1, 1e9)).limit).toBe('max_total_points');
    });
  });
});
