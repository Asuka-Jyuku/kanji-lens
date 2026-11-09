import { TestBed } from '@angular/core/testing';
import { App } from './app';

describe('App', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [App] }).compileComponents();
  });

  it('shows the title and the drawing area, in Portuguese, the source language (ADR 0009)', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;

    expect(page.querySelector('h1')?.textContent).toBe('KanjiLens');
    expect(page.querySelector('app-drawing-pad .instruction')?.textContent?.trim()).toBe(
      'Desenhe um kanji',
    );
    expect(page.querySelector('app-drawing-pad canvas')).not.toBeNull();
  });

  it('shows the stroke order mode before the drawing area (ADR 0012)', async () => {
    const fixture = TestBed.createComponent(App);
    await fixture.whenStable();
    const page = fixture.nativeElement as HTMLElement;

    const selector = page.querySelector('app-mode-selector');
    const pad = page.querySelector('app-drawing-pad');
    expect(selector?.querySelector('legend')?.textContent?.trim()).toBe('Ordem dos traços');
    expect(selector!.compareDocumentPosition(pad!) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  });
});
