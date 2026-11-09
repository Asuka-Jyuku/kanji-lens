import { Injectable, signal } from '@angular/core';

import { DEFAULT_STROKE_ORDER_MODE, StrokeOrderMode } from '../domain/stroke-order-mode';

/**
 * The stroke order mode chosen for the next recognition, as a signal for the screen.
 * Sending the drawing (#58) reads `mode` next to `DrawingSession.drawing`. Kept apart from
 * the drawing: choosing a mode never touches the strokes. Not remembered between visits;
 * ADR 0012 has the mode picked for each recognition.
 */
@Injectable({ providedIn: 'root' })
export class StrokeOrderModeSelection {
  private readonly chosen = signal<StrokeOrderMode>(DEFAULT_STROKE_ORDER_MODE);

  readonly mode = this.chosen.asReadonly();

  choose(mode: StrokeOrderMode): void {
    this.chosen.set(mode);
  }
}
