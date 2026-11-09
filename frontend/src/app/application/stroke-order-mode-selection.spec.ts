import { TestBed } from '@angular/core/testing';

import { DrawingSession } from './drawing-session';
import { StrokeOrderModeSelection } from './stroke-order-mode-selection';

describe('StrokeOrderModeSelection', () => {
  let selection: StrokeOrderModeSelection;
  let session: DrawingSession;

  beforeEach(() => {
    selection = TestBed.inject(StrokeOrderModeSelection);
    session = TestBed.inject(DrawingSession);
  });

  it('starts with the order not mattering', () => {
    expect(selection.mode()).toBe('unordered');
  });

  it('keeps the mode chosen, and lets it go back', () => {
    selection.choose('ordered');
    expect(selection.mode()).toBe('ordered');

    selection.choose('unordered');
    expect(selection.mode()).toBe('unordered');
  });

  it('leaves the drawing as it is when the mode changes', () => {
    session.resize({ width: 320, height: 320 });
    session.startStroke({ x: 10, y: 10, time: 0 });
    session.extendStroke({ x: 50, y: 60, time: 16 });
    session.endStroke();
    const before = session.drawing();

    selection.choose('ordered');

    expect(session.drawing()).toBe(before);
  });
});
