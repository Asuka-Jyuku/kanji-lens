import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { DrawingPad } from './presentation/drawing-pad/drawing-pad';
import { ModeSelector } from './presentation/mode-selector/mode-selector';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, ModeSelector, DrawingPad],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {}
