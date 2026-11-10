import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawingSession } from '../../application/drawing-session';
import { FileDownload } from '../../application/file-download';
import { DrawingExport } from './drawing-export';

class FakeFileDownload extends FileDownload {
  readonly saved: { fileName: string; content: string }[] = [];

  save(fileName: string, content: string): void {
    this.saved.push({ fileName, content });
  }
}

describe('DrawingExport', () => {
  let fixture: ComponentFixture<DrawingExport>;
  let page: HTMLElement;
  let session: DrawingSession;
  let download: FakeFileDownload;

  beforeEach(async () => {
    download = new FakeFileDownload();
    await TestBed.configureTestingModule({
      imports: [DrawingExport],
      providers: [{ provide: FileDownload, useValue: download }],
    }).compileComponents();
    fixture = TestBed.createComponent(DrawingExport);
    page = fixture.nativeElement as HTMLElement;
    session = TestBed.inject(DrawingSession);
    session.resize({ width: 320, height: 320 });
    await fixture.whenStable();
  });

  function drawStrokes(count: number) {
    for (let i = 0; i < count; i++) {
      session.startStroke({ x: 20 + i * 10, y: 20, time: i * 100 });
      session.extendStroke({ x: 20 + i * 10, y: 80, time: i * 100 + 50 });
      session.endStroke();
    }
  }

  function type(selector: string, value: string) {
    const field = page.querySelector(selector) as HTMLInputElement | HTMLSelectElement;
    field.value = value;
    field.dispatchEvent(new Event(field instanceof HTMLSelectElement ? 'change' : 'input'));
  }

  async function submit() {
    (page.querySelector('button.save') as HTMLButtonElement).click();
    await fixture.whenStable();
  }

  const status = () => page.querySelector('[role="status"]')?.textContent?.trim();

  it('is closed by default, below the drawing, with a save button off while nothing is drawn', () => {
    expect((page.querySelector('details') as HTMLDetailsElement).open).toBe(false);
    expect(page.querySelector('summary')?.textContent).toContain('Exportar desenho');
    expect((page.querySelector('button.save') as HTMLButtonElement).disabled).toBe(true);
  });

  it('saves the drawing with the kanji and the mistake, and says the file name', async () => {
    drawStrokes(3);
    await fixture.whenStable();
    type('input[lang="ja"]', ' 川 ');
    type('select', 'order');
    type('input[inputmode="numeric"]', '3, 2');
    await submit();

    expect(download.saved).toHaveLength(1);
    const sample = JSON.parse(download.saved[0].content);
    expect(sample.label).toEqual({ kanji: '川', stroke_order: 'order', strokes: [2, 3] });
    expect(sample.request.strokes).toHaveLength(3);
    expect(status()).toContain(download.saved[0].fileName);
  });

  it('asks for one kanji before saving', async () => {
    drawStrokes(1);
    await fixture.whenStable();
    type('input[lang="ja"]', 'abc');
    await submit();

    expect(download.saved).toEqual([]);
    expect(status()).toContain('Escreva um kanji só');
  });

  it('refuses a stroke number the drawing does not have', async () => {
    drawStrokes(2);
    await fixture.whenStable();
    type('input[lang="ja"]', '二');
    type('select', 'direction');
    type('input[inputmode="numeric"]', '5');
    await submit();

    expect(download.saved).toEqual([]);
    expect(status()).toContain('números de traço');
  });

  it('turns the stroke numbers off when the order is right', async () => {
    const strokes = page.querySelector('input[inputmode="numeric"]') as HTMLInputElement;
    expect(strokes.disabled).toBe(true);

    type('select', 'broken');
    await fixture.whenStable();

    expect(strokes.disabled).toBe(false);
  });
});
