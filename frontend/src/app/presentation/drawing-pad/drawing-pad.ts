import {
  ChangeDetectionStrategy,
  Component,
  DestroyRef,
  ElementRef,
  afterNextRender,
  afterRenderEffect,
  inject,
  viewChild,
} from '@angular/core';

import { DrawingSession } from '../../application/drawing-session';
import type { Drawing, PointerSample } from '../../domain/drawing';

/**
 * The drawing area of the recognition screen: mouse, touch and pen through Pointer Events,
 * one pointer at a time, with "Desfazer" and "Limpar" (docs/UI-UX.md, "Padrões propostos";
 * angular-conventions, references/style.md, "Canvas e touch").
 */
@Component({
  selector: 'app-drawing-pad',
  templateUrl: './drawing-pad.html',
  styleUrl: './drawing-pad.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DrawingPad {
  protected readonly session = inject(DrawingSession);
  private readonly canvasRef = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');
  /** The pointer drawing the open stroke; a second finger is ignored until it lifts. */
  private activePointer: number | null = null;
  /** The canvas box when the stroke started: the page does not move while drawing. */
  private box: DOMRect | null = null;
  /** Asked once; null where there is no 2D context (jsdom), and then nothing is painted. */
  private context: CanvasRenderingContext2D | null | undefined;

  constructor() {
    const destroyRef = inject(DestroyRef);
    afterNextRender(() => {
      this.measure();
      // Not in every runtime (jsdom has none); the size is measured again on each pointerdown.
      if (typeof ResizeObserver === 'undefined') {
        return;
      }
      const observer = new ResizeObserver(() => this.measure());
      observer.observe(this.canvas);
      destroyRef.onDestroy(() => observer.disconnect());
    });
    afterRenderEffect(() => this.render(this.session.drawing()));
  }

  protected onPointerDown(event: PointerEvent): void {
    if (this.activePointer !== null || (event.pointerType === 'mouse' && event.button !== 0)) {
      return;
    }
    event.preventDefault();
    this.measure();
    this.box = this.canvas.getBoundingClientRect();
    // Keeps the stroke going when the finger leaves the canvas (not in every runtime).
    this.canvas.setPointerCapture?.(event.pointerId);
    this.activePointer = event.pointerId;
    this.session.startStroke(this.sample(event));
  }

  protected onPointerMove(event: PointerEvent): void {
    if (event.pointerId !== this.activePointer) {
      return;
    }
    // Coalesced events carry the points the browser merged into this one: a smoother stroke.
    const coalesced = event.getCoalescedEvents?.() ?? [];
    for (const each of coalesced.length > 0 ? coalesced : [event]) {
      this.session.extendStroke(this.sample(each));
    }
  }

  protected onPointerEnd(event: PointerEvent): void {
    if (event.pointerId !== this.activePointer) {
      return;
    }
    this.activePointer = null;
    this.box = null;
    this.session.endStroke();
  }

  private get canvas(): HTMLCanvasElement {
    return this.canvasRef().nativeElement;
  }

  private sample(event: PointerEvent): PointerSample {
    const box = this.box ?? this.canvas.getBoundingClientRect();
    return { x: event.clientX - box.left, y: event.clientY - box.top, time: event.timeStamp };
  }

  /** The CSS size goes to the session; the bitmap follows the pixel ratio, for a sharp stroke. */
  private measure(): void {
    const { width, height } = this.canvas.getBoundingClientRect();
    if (width <= 0 || height <= 0) {
      return;
    }
    const ratio = window.devicePixelRatio || 1;
    this.canvas.width = Math.round(width * ratio);
    this.canvas.height = Math.round(height * ratio);
    this.session.resize({ width, height });
    this.render(this.session.drawing());
  }

  private render(drawing: Drawing): void {
    if (this.context === undefined) {
      this.context = this.canvas.getContext('2d');
    }
    const context = this.context;
    if (!context) {
      return;
    }
    const ratio = this.canvas.width / (drawing.canvas.width || this.canvas.width || 1);
    context.setTransform(1, 0, 0, 1, 0, 0);
    context.clearRect(0, 0, this.canvas.width, this.canvas.height);
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    // The ink is the canvas' CSS color, so the stroke follows the theme and its contrast.
    const ink = getComputedStyle(this.canvas).color;
    const lineWidth = Math.max(3, drawing.canvas.width / 40);
    context.strokeStyle = ink;
    context.fillStyle = ink;
    context.lineWidth = lineWidth;
    context.lineCap = 'round';
    context.lineJoin = 'round';
    for (const stroke of drawing.strokes) {
      if (stroke.length === 1) {
        context.beginPath();
        context.arc(stroke[0].x, stroke[0].y, lineWidth / 2, 0, 2 * Math.PI);
        context.fill();
        continue;
      }
      context.beginPath();
      context.moveTo(stroke[0].x, stroke[0].y);
      for (const point of stroke.slice(1)) {
        context.lineTo(point.x, point.y);
      }
      context.stroke();
    }
  }
}
