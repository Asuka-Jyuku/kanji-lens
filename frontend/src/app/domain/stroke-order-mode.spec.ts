import { DEFAULT_STROKE_ORDER_MODE, isStrokeOrderMode } from './stroke-order-mode';

describe('stroke order mode', () => {
  it('starts as "order does not matter" (ADR 0012)', () => {
    expect(DEFAULT_STROKE_ORDER_MODE).toBe('unordered');
  });

  it('accepts only the two modes the API takes', () => {
    expect(isStrokeOrderMode('ordered')).toBe(true);
    expect(isStrokeOrderMode('unordered')).toBe(true);
    for (const other of ['', 'Ordered', 'on', null, undefined, 1]) {
      expect(isStrokeOrderMode(other)).toBe(false);
    }
  });
});
