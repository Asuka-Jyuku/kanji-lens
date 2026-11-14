import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawingSession } from '../../application/drawing-session';
import { BrowserFileDownload } from '../drawing-export/browser-file-download';
import { CollectionSession } from './collection-session';

class FakeFileDownload {
  readonly saved: { fileName: string; content: string; mediaType: string }[] = [];

  save(fileName: string, content: string, mediaType: string): void {
    this.saved.push({ fileName, content, mediaType });
  }
}

describe('CollectionSession', () => {
  let fixture: ComponentFixture<CollectionSession>;
  let page: HTMLElement;
  let session: DrawingSession;
  let download: FakeFileDownload;

  beforeEach(async () => {
    download = new FakeFileDownload();
    await TestBed.configureTestingModule({
      imports: [CollectionSession],
      providers: [{ provide: BrowserFileDownload, useValue: download }],
    }).compileComponents();
    fixture = TestBed.createComponent(CollectionSession);
    page = fixture.nativeElement as HTMLElement;
    session = TestBed.inject(DrawingSession);
    session.resize({ width: 320, height: 320 });
    await fixture.whenStable();
  });

  async function draw() {
    session.startStroke({ x: 20, y: 20, time: 0 });
    session.extendStroke({ x: 20, y: 80, time: 50 });
    session.endStroke();
    await fixture.whenStable();
  }

  function type(selector: string, value: string) {
    const field = page.querySelector(selector) as HTMLInputElement | HTMLTextAreaElement;
    field.value = value;
    field.dispatchEvent(new Event('input'));
  }

  async function click(selector: string) {
    (page.querySelector(selector) as HTMLButtonElement).click();
    await fixture.whenStable();
  }

  async function start(writer: string, kanji: string, repetitions: string) {
    type('input[type="text"]', writer);
    type('textarea', kanji);
    type('input[type="number"]', repetitions);
    await click('button.start');
  }

  const asked = () => page.querySelector('.bar .kanji')?.textContent?.trim();
  const barStatus = () => page.querySelector('.bar [role="status"]')?.textContent?.trim();
  const formStatus = () => page.querySelector('form [role="status"]')?.textContent?.trim();

  it('is closed by default, with the 40 first classes and 5 times each already filled in', () => {
    expect((page.querySelector('details') as HTMLDetailsElement).open).toBe(false);
    expect(page.querySelector('summary')?.textContent).toContain('Sessão de coleta');
    expect((page.querySelector('textarea') as HTMLTextAreaElement).value).toHaveLength(40);
    expect((page.querySelector('input[type="number"]') as HTMLInputElement).value).toBe('5');
    expect(page.querySelector('.bar')).toBeNull();
  });

  it('asks for a code, not a name, before starting', async () => {
    await start('Ana Lima', '日目', '1');

    expect(page.querySelector('.bar')).toBeNull();
    expect(formStatus()).toContain('código');
  });

  it('refuses a list that is not kanji, or a number of times out of range', async () => {
    await start('a', '日 x', '1');
    expect(formStatus()).toContain('só kanji');

    await start('a', '日目', '0');
    expect(formStatus()).toContain('de 1 a 20');
    expect(page.querySelector('.bar')).toBeNull();
  });

  it('asks for each kanji in turn, saves it with the answer key, and clears the canvas', async () => {
    session.chooseMode('ordered');
    await draw();
    // A phone keyboard starts with a capital letter; the code is kept lowercase.
    await start('P2', '日目', '1');
    expect(session.empty()).toBe(true);
    const first = asked() as string;
    expect(['日', '目']).toContain(first);
    expect(page.querySelector('.bar .kanji')?.getAttribute('lang')).toBe('ja');
    expect(page.querySelector('.bar .progress')?.textContent).toContain('1 de 2');
    expect((page.querySelector('button.save') as HTMLButtonElement).disabled).toBe(true);

    await draw();
    await click('button.save');

    expect(session.empty()).toBe(true);
    expect(asked()).not.toBe(first);
    expect(page.querySelector('.bar .progress')?.textContent).toContain('2 de 2');

    await click('button.download');
    expect(download.saved).toHaveLength(1);
    const batch = JSON.parse(download.saved[0].content);
    expect(batch.format).toBe('kanjilens-drawing-batch');
    expect(batch.writer).toBe('p2');
    expect(batch.samples).toHaveLength(1);
    expect(batch.samples[0].label).toEqual({ kanji: first, stroke_order: 'correct', strokes: [] });
    expect(batch.samples[0].request.stroke_order_mode).toBe('ordered');
    expect(download.saved[0].fileName).toMatch(/^batch-p2-\d{8}T\d{6}Z\.json$/);
    expect(barStatus()).toContain(download.saved[0].fileName);
  });

  it('skips a kanji without saving it, and says when the queue is over', async () => {
    await start('a', '日目', '1');
    await click('button.skip');
    await click('button.skip');

    expect(page.querySelector('.bar .prompt')?.textContent).toContain('Fila terminada');
    expect((page.querySelector('button.skip') as HTMLButtonElement).disabled).toBe(true);
    expect((page.querySelector('button.download') as HTMLButtonElement).disabled).toBe(true);
  });

  it('does not end while drawings were not downloaded, and warns before leaving the page', async () => {
    await start('a', '日目', '1');
    await draw();
    await click('button.save');

    const leaving = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(leaving);
    expect(leaving.defaultPrevented).toBe(true);

    await click('button.end');
    expect(page.querySelector('.bar')).not.toBeNull();
    expect(barStatus()).toContain('Baixe o lote antes de encerrar');

    await click('button.download');
    await click('button.end');
    expect(page.querySelector('.bar')).toBeNull();

    const leavingNow = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(leavingNow);
    expect(leavingNow.defaultPrevented).toBe(false);
  });
});
