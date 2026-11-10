import { ChangeDetectionStrategy, Component, computed, inject } from '@angular/core';

import { RecognizeDrawing } from '../../application/recognize-drawing.use-case';

/**
 * "Reconhecer" and the job's state, always in view and announced (docs/UI-UX.md, "O estado do
 * job sempre visível" and "Reconhecer desabilitado com o canvas vazio"). Each error says what
 * went wrong and what to do (WCAG 3.3.1). The candidates themselves are the result screen's
 * (#59); here, only the best one, so a finished job shows something.
 */
@Component({
  selector: 'app-recognition-panel',
  templateUrl: './recognition-panel.html',
  styleUrl: './recognition-panel.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class RecognitionPanel {
  protected readonly recognition = inject(RecognizeDrawing);
  protected readonly state = this.recognition.state;
  protected readonly best = computed(() => this.recognition.result()?.predictions?.[0] ?? null);
  protected readonly failure = computed(() => {
    const state = this.state();
    return state.phase === 'failed' ? state : null;
  });
}
