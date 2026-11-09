import { ChangeDetectionStrategy, Component } from '@angular/core';
import { RouterOutlet } from '@angular/router';

import { DrawingPad } from './presentation/drawing-pad/drawing-pad';

@Component({
  selector: 'app-root',
  imports: [RouterOutlet, DrawingPad],
  templateUrl: './app.html',
  styleUrl: './app.css',
  changeDetection: ChangeDetectionStrategy.OnPush,
})
export class App {}
