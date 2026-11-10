import { DRAWING_LIMITS } from '../domain/drawing';
import { DrawingSession } from './drawing-session';

describe('DrawingSession', () => {
  function session(): DrawingSession {
    const created = new DrawingSession();
    created.resize({ width: 320, height: 320 });
    return created;
  }

  it('exposes the drawing and whether it is empty', () => {
    const drawing = session();
    expect(drawing.empty()).toBe(true);

    drawing.startStroke({ x: 10, y: 10, time: 50 });
    drawing.extendStroke({ x: 20, y: 20, time: 70 });
    drawing.endStroke();

    expect(drawing.empty()).toBe(false);
    expect(drawing.drawing().strokes).toEqual([
      [
        { x: 10, y: 10, t: 0 },
        { x: 20, y: 20, t: 20 },
      ],
    ]);
  });

  it('remembers the limit a refused point hit, until the drawing shrinks', () => {
    const drawing = session();
    for (let i = 0; i < DRAWING_LIMITS.maxStrokes; i++) {
      drawing.startStroke({ x: i, y: i, time: i });
      drawing.endStroke();
    }
    expect(drawing.limit()).toBeNull();

    drawing.startStroke({ x: 1, y: 1, time: 999 });
    expect(drawing.limit()).toBe('max_strokes');

    drawing.undo();
    expect(drawing.limit()).toBeNull();
    expect(drawing.drawing().strokes).toHaveLength(DRAWING_LIMITS.maxStrokes - 1);
  });

  it('clears the drawing and the limit', () => {
    const drawing = session();
    drawing.startStroke({ x: 1, y: 1, time: 0 });
    drawing.endStroke();

    drawing.clear();

    expect(drawing.empty()).toBe(true);
    expect(drawing.limit()).toBeNull();
    expect(drawing.drawing().canvas).toEqual({ width: 320, height: 320 });
  });

  it('starts with the order not mattering, and changing the mode keeps the drawing', () => {
    const drawing = session();
    drawing.startStroke({ x: 10, y: 10, time: 0 });
    drawing.extendStroke({ x: 50, y: 60, time: 16 });
    drawing.endStroke();
    const before = drawing.drawing();
    expect(drawing.mode()).toBe('unordered');

    drawing.chooseMode('ordered');

    expect(drawing.mode()).toBe('ordered');
    expect(drawing.drawing()).toBe(before);
  });
});
