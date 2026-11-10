import { ChangeDetectionStrategy, Component } from '@angular/core';
import { NgComponentOutlet } from '@angular/common';

import { DEV_TOOL } from './app.dev-tools';
import { DrawingPad } from './presentation/drawing-pad/drawing-pad';
import { ModeSelector } from './presentation/mode-selector/mode-selector';
import { RecognitionPanel } from './presentation/recognition-panel/recognition-panel';

@Component({
  selector: 'app-root',
  imports: [NgComponentOutlet, ModeSelector, DrawingPad, RecognitionPanel],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {
  /** The development-only tool, below the drawing; none in the production build (app.dev-tools.ts). */
  protected readonly devTool = DEV_TOOL;
}
