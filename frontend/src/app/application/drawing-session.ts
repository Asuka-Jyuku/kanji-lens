import { Injectable, computed, signal } from '@angular/core';

import {
  CanvasSize,
  CaptureUpdate,
  DrawingCapture,
  DrawingLimit,
  PointerSample,
  clearDrawing,
  emptyCapture,
  endStroke,
  extendStroke,
  isEmpty,
  resizeCanvas,
  startStroke,
  undoLastStroke,
} from '../domain/drawing';
import { DEFAULT_STROKE_ORDER_MODE, StrokeOrderMode } from '../domain/stroke-order-mode';

/**
 * The drawing being made and the stroke order mode chosen for it, as signals for the screen
 * (ADR 0004: the component only reads). The canvas feeds it pointer samples; sending the
 * drawing (#58) reads `drawing` and `mode`. Choosing a mode never touches the strokes, and the
 * mode is not remembered between visits (ADR 0012).
 */
@Injectable({ providedIn: 'root' })
export class DrawingSession {
  private readonly capture = signal<DrawingCapture>(emptyCapture({ width: 0, height: 0 }));
  private readonly lastLimit = signal<DrawingLimit | null>(null);
  private readonly chosenMode = signal<StrokeOrderMode>(DEFAULT_STROKE_ORDER_MODE);

  readonly drawing = computed(() => this.capture().drawing);
  readonly empty = computed(() => isEmpty(this.drawing()));
  /** The limit the last refused point hit; cleared when the drawing shrinks. */
  readonly limit = this.lastLimit.asReadonly();
  readonly mode = this.chosenMode.asReadonly();

  chooseMode(mode: StrokeOrderMode): void {
    this.chosenMode.set(mode);
  }

  startStroke(sample: PointerSample): void {
    this.apply(startStroke(this.capture(), sample));
  }

  extendStroke(sample: PointerSample): void {
    this.apply(extendStroke(this.capture(), sample));
  }

  endStroke(): void {
    this.capture.update(endStroke);
  }

  undo(): void {
    this.capture.update(undoLastStroke);
    this.lastLimit.set(null);
  }

  clear(): void {
    this.capture.update(clearDrawing);
    this.lastLimit.set(null);
  }

  resize(canvas: CanvasSize): void {
    this.capture.update((capture) => resizeCanvas(capture, canvas));
  }

  private apply(update: CaptureUpdate): void {
    this.capture.set(update.capture);
    if (update.limit) {
      this.lastLimit.set(update.limit);
    }
  }
}
