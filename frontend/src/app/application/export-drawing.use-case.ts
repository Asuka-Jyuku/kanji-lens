import { Injectable, inject } from '@angular/core';

import {
  DrawingLabel,
  drawingSample,
  sampleFileName,
  serializeSample,
} from '../domain/drawing-sample';
import { isEmpty } from '../domain/drawing';
import { DrawingSession } from './drawing-session';
import { FileDownload } from './file-download';
import { StrokeOrderModeSelection } from './stroke-order-mode-selection';

/**
 * Saves the drawing on screen as a test sample, with its answer key (#66). Development builds
 * only: the screen that calls it is left out of the production build (app.dev-tools.ts).
 */
@Injectable({ providedIn: 'root' })
export class ExportDrawing {
  private readonly session = inject(DrawingSession);
  private readonly modeSelection = inject(StrokeOrderModeSelection);
  private readonly download = inject(FileDownload);

  /** The name of the file saved, or `null` when there is nothing drawn. */
  export(label: DrawingLabel, now: Date = new Date()): string | null {
    const drawing = this.session.drawing();
    if (isEmpty(drawing)) {
      return null;
    }
    const sample = drawingSample(drawing, this.modeSelection.mode(), label, now);
    const fileName = sampleFileName(sample);
    this.download.save(fileName, serializeSample(sample), 'application/json');
    return fileName;
  }
}
