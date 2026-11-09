import { ChangeDetectionStrategy, Component, inject } from '@angular/core';

import { StrokeOrderModeSelection } from '../../application/stroke-order-mode-selection';
import { isStrokeOrderMode } from '../../domain/stroke-order-mode';

/**
 * "Ordem dos traços: importa / não importa", always in view before drawing (ADR 0012;
 * docs/UI-UX.md, "Seletor de modo visível antes de desenhar"). Two native radios, not a
 * switch: the choice only shows in the next recognition.
 */
@Component({
  selector: 'app-mode-selector',
  templateUrl: './mode-selector.html',
  styleUrl: './mode-selector.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class ModeSelector {
  protected readonly selection = inject(StrokeOrderModeSelection);

  protected onChange(event: Event): void {
    const { value } = event.target as HTMLInputElement;
    if (isStrokeOrderMode(value)) {
      this.selection.choose(value);
    }
  }
}
