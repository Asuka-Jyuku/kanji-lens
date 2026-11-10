import { ChangeDetectionStrategy, Component, computed, inject, linkedSignal } from '@angular/core';

import { RecognizeDrawing } from '../../application/recognize-drawing.use-case';
import { confidencePercent, strokeOrderFeedback } from '../../domain/stroke-order-feedback';

/**
 * The candidates, best first, with their confidence (docs/UI-UX.md, "Candidatos como lista").
 * In the `ordered` mode each candidate is a button: the student picks the kanji they meant and
 * reads, in words, how its stroke order went (ADRs 0012 and 0016). The best one starts picked.
 */
@Component({
  selector: 'app-prediction-list',
  templateUrl: './prediction-list.html',
  styleUrl: './prediction-list.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class PredictionList {
  private readonly job = inject(RecognizeDrawing).result;

  protected readonly predictions = computed(() => this.job()?.predictions ?? []);
  protected readonly ordered = computed(() => this.job()?.strokeOrderMode === 'ordered');
  /** Back to the best candidate whenever a new result arrives. */
  protected readonly picked = linkedSignal({ source: this.predictions, computation: () => 0 });
  protected readonly pickedKanji = computed(() => this.predictions()[this.picked()]?.kanji ?? '');
  protected readonly feedback = computed(() => {
    const evaluation = this.predictions()[this.picked()]?.strokeOrder;
    return evaluation ? strokeOrderFeedback(evaluation) : null;
  });
  protected readonly percent = confidencePercent;
}
