import { TestBed } from '@angular/core/testing';

import { App } from './app';
import { RecognitionGateway } from './application/recognition.gateway';
import { ResultStream } from './application/result-stream';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [App],
      // The page only renders here; nothing is sent.
      providers: [
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
    expect(order).toEqual([
      'app-mode-selector',
      'app-drawing-pad',
      'app-recognition-panel',
      'app-prediction-list',
    ]);
  });
});
