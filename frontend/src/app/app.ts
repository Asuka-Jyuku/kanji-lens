import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NgComponentOutlet } from '@angular/common';

import { DEV_TOOLS } from './app.dev-tools';
import { DrawingPad } from './presentation/drawing-pad/drawing-pad';
import { ModeSelector } from './presentation/mode-selector/mode-selector';
import { PredictionList } from './presentation/prediction-list/prediction-list';
import { RecognitionPanel } from './presentation/recognition-panel/recognition-panel';

@Component({
  selector: 'app-root',
  imports: [NgComponentOutlet, ModeSelector, DrawingPad, RecognitionPanel, PredictionList],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  /** The development-only tools, below the drawing; none in the production build (app.dev-tools.ts). */
  protected readonly devTools = DEV_TOOLS;
}
