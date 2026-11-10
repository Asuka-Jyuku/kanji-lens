import { TestBed } from '@angular/core/testing';

import { DrawingSession } from './drawing-session';
import { ExportDrawing } from './export-drawing.use-case';
import { FileDownload } from './file-download';
import { StrokeOrderModeSelection } from './stroke-order-mode-selection';

class FakeFileDownload extends FileDownload {
  readonly saved: { fileName: string; content: string; mediaType: string }[] = [];

  save(fileName: string, content: string, mediaType: string): void {
    this.saved.push({ fileName, content, mediaType });
  }
}

describe('ExportDrawing', () => {
  let download: FakeFileDownload;
  let session: DrawingSession;
  let exportDrawing: ExportDrawing;
  const at = new Date(Date.UTC(2026, 10, 10, 9, 0, 0));

  beforeEach(() => {
    download = new FakeFileDownload();
    TestBed.configureTestingModule({ providers: [{ provide: FileDownload, useValue: download }] });
    session = TestBed.inject(DrawingSession);
    exportDrawing = TestBed.inject(ExportDrawing);
    session.resize({ width: 320, height: 320 });
  });

  it('saves the drawing on screen, with the chosen mode and the answer key, as JSON', () => {
    TestBed.inject(StrokeOrderModeSelection).choose('ordered');
    session.startStroke({ x: 10, y: 20, time: 1000 });
    session.extendStroke({ x: 10, y: 80, time: 1100 });
    session.endStroke();

    const fileName = exportDrawing.export(
      { kanji: '十', stroke_order: 'correct', strokes: [] },
      at,
    );

    expect(fileName).toBe('u5341-correct-20261110T090000Z.json');
    expect(download.saved).toHaveLength(1);
    const [{ content, mediaType }] = download.saved;
    expect(mediaType).toBe('application/json');
    expect(JSON.parse(content)).toEqual({
      format: 'kanjilens-drawing',
      version: 1,
      exported_at: '2026-11-10T09:00:00.000Z',
      label: { kanji: '十', stroke_order: 'correct', strokes: [] },
      request: {
        stroke_order_mode: 'ordered',
        canvas: { width: 320, height: 320 },
        strokes: [
          [
            [10, 20, 0],
            [10, 80, 100],
          ],
        ],
      },
    });
  });

  it('saves nothing when there is nothing drawn', () => {
    expect(exportDrawing.export({ kanji: '十', stroke_order: 'correct', strokes: [] }, at)).toBe(
      null,
    );
    expect(download.saved).toEqual([]);
  });

  it('leaves the drawing as it was', () => {
    session.startStroke({ x: 10, y: 20, time: 0 });
    session.endStroke();
    const before = session.drawing();

    exportDrawing.export({ kanji: '一', stroke_order: 'correct', strokes: [] }, at);

    expect(session.drawing()).toBe(before);
  });
});
