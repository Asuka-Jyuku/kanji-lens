import { Injectable, computed, signal } from '@angular/core';

import {
  CanvasSize,
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

/**
 * The drawing being made, as signals for the screen (ADR 0004: the component only reads).
 * The canvas feeds it pointer samples; sending the drawing to the API (#58) reads `drawing`.
 */
@Injectable({ providedIn: 'root' })
export class DrawingSession {
  private readonly capture = signal<DrawingCapture>(emptyCapture({ width: 0, height: 0 }));
  private readonly lastLimit = signal<DrawingLimit | null>(null);

  readonly drawing = computed(() => this.capture().drawing);
  readonly empty = computed(() => isEmpty(this.drawing()));
  /** The limit the last refused point hit; cleared when the drawing shrinks. */
  readonly limit = this.lastLimit.asReadonly();

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

  private apply(update: { capture: DrawingCapture; limit?: DrawingLimit }): void {
    this.capture.set(update.capture);
    if (update.limit) {
      this.lastLimit.set(update.limit);
    }
  }
}
