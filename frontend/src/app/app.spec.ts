import { TestBed } from '@angular/core/testing';

import { App } from './app';
// The tests run on the development build, so this is app.dev-tools.development.ts.
import { DEV_PROVIDERS } from './app.dev-tools';
import { RecognitionGateway } from './application/recognition.gateway';
import { ResultStream } from './application/result-stream';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      // The page only renders here; nothing is sent.
      providers: [
        ...DEV_PROVIDERS,
        { provide: RecognitionGateway, useValue: {} },
        { provide: ResultStream, useValue: {} },
      ],
    }).compileComponents();
  });

  it('shows the title, the mode, the drawing area and "Reconhecer", in Portuguese, the source language (ADR 0009)', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;

    expect(page.querySelector('h1')?.textContent).toBe('KanjiLens');
    expect(page.querySelector('app-drawing-pad .instruction')?.textContent?.trim()).toBe(
      'Desenhe um kanji',
    );
    expect(page.querySelector('app-drawing-pad canvas')).not.toBeNull();
    expect(page.querySelector('app-mode-selector legend')?.textContent?.trim()).toBe(
      'Ordem dos traços',
    );
    expect(page.querySelector('app-recognition-panel button')?.textContent?.trim()).toBe(
      'Reconhecer',
    );
  });

  it('puts the mode before the drawing, and "Reconhecer" after it', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;

    const order = Array.from(page.querySelectorAll('.workspace > *')).map((each) =>
      each.tagName.toLowerCase(),
    );
    expect(order).toEqual(['app-mode-selector', 'app-drawing-pad', 'app-recognition-panel']);
  });

  it('shows the drawing export below the drawing area in the development build (#66)', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;

    const pad = page.querySelector('app-drawing-pad');
    const tool = page.querySelector('app-drawing-export');
    expect(tool).not.toBeNull();
    expect(pad!.compareDocumentPosition(tool!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
