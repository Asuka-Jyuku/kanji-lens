import { ChangeDetectionStrategy, Component, computed, inject, signal } from '@angular/core';

import { DrawingSession } from '../../application/drawing-session';
import { ExportDrawing } from '../../application/export-drawing.use-case';
import {
  StrokeOrderLabel,
  isSingleKanji,
  isStrokeOrderLabel,
  parseStrokeNumbers,
} from '../../domain/drawing-sample';

/** Why the file was not saved; the template turns it into a message (ADR 0009). */
type ExportProblem = 'kanji' | 'strokes';

/**
 * "Exportar desenho": saves the drawing with the kanji meant and the stroke order used, to
 * build the test sets (#66; docs/MODEL.md, "Desenhos do canvas"). Development builds only
 * (app.dev-tools.ts). Closed by default, below the drawing, so it never gets in its way.
 */
@Component({
  selector: 'app-drawing-export',
  templateUrl: './drawing-export.html',
  styleUrl: './drawing-export.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class DrawingExport {
  protected readonly session = inject(DrawingSession);
  private readonly exportDrawing = inject(ExportDrawing);

  protected readonly kanji = signal('');
  protected readonly strokeOrder = signal<StrokeOrderLabel>('correct');
  protected readonly strokes = signal('');
  protected readonly problem = signal<ExportProblem | null>(null);
  protected readonly saved = signal<string | null>(null);
  protected readonly isCorrect = computed(() => this.strokeOrder() === 'correct');

  protected onKanji(event: Event): void {
    this.kanji.set((event.target as HTMLInputElement).value.trim());
  }

  protected onStrokeOrder(event: Event): void {
    const { value } = event.target as HTMLSelectElement;
    if (isStrokeOrderLabel(value)) {
      this.strokeOrder.set(value);
    }
  }

  protected onStrokes(event: Event): void {
    this.strokes.set((event.target as HTMLInputElement).value);
  }

  protected onSubmit(event: Event): void {
    event.preventDefault();
    this.saved.set(null);
    if (!isSingleKanji(this.kanji())) {
      this.problem.set('kanji');
      return;
    }
    const strokeCount = this.session.drawing().strokes.length;
    const strokes = this.isCorrect() ? [] : parseStrokeNumbers(this.strokes(), strokeCount);
    if (strokes === null) {
      this.problem.set('strokes');
      return;
    }
    this.problem.set(null);
    this.saved.set(
      this.exportDrawing.export({
        kanji: this.kanji(),
        stroke_order: this.strokeOrder(),
        strokes,
      }),
    );
  }
}
