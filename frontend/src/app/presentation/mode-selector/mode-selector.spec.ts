import { ComponentFixture, TestBed } from '@angular/core/testing';

import { DrawingSession } from '../../application/drawing-session';
import { ModeSelector } from './mode-selector';

describe('ModeSelector', () => {
  let fixture: ComponentFixture<ModeSelector>;
  let page: HTMLElement;
  let session: DrawingSession;

  beforeEach(async () => {
    await TestBed.configureTestingModule({ imports: [ModeSelector] }).compileComponents();
    fixture = TestBed.createComponent(ModeSelector);
    page = fixture.nativeElement as HTMLElement;
    session = TestBed.inject(DrawingSession);
    await fixture.whenStable();
  });

  function radio(mode: 'ordered' | 'unordered'): HTMLInputElement {
    return page.querySelector(`input[value="${mode}"]`) as HTMLInputElement;
  }

  it('is a labelled group of two radios, with the label text visible', () => {
    const fieldset = page.querySelector('fieldset');
    expect(fieldset?.querySelector('legend')?.textContent?.trim()).toBe('Ordem dos traços');

    const radios = Array.from(page.querySelectorAll<HTMLInputElement>('input[type="radio"]'));
    expect(radios).toHaveLength(2);
    // One name: the browser makes them one group, moved through with the arrow keys.
    expect(new Set(radios.map((each) => each.name)).size).toBe(1);
    expect(radios.map((each) => each.closest('label')?.textContent?.trim())).toEqual([
      'Importa',
      'Não importa',
    ]);
  });

  it('starts with "Não importa" chosen', () => {
    expect(radio('unordered').checked).toBe(true);
    expect(radio('ordered').checked).toBe(false);
    expect(session.mode()).toBe('unordered');
  });

  it('hands over the mode chosen, and shows it', async () => {
    radio('ordered').click();
    await fixture.whenStable();

    expect(session.mode()).toBe('ordered');
    expect(radio('ordered').checked).toBe(true);
    expect(radio('unordered').checked).toBe(false);
  });

  it('follows the mode when it changes elsewhere', async () => {
    session.chooseMode('ordered');
    await fixture.whenStable();

    expect(radio('ordered').checked).toBe(true);
  });

  it('takes a choice made by keyboard, on a focused radio', async () => {
    // jsdom does not move through a radio group with the arrow keys or Space; the browser
    // does, since the radios are native (checked in Chromium, see the PR). What the component
    // owns is the change event the browser fires then, which is what this sends.
    radio('ordered').focus();
    expect(document.activeElement).toBe(radio('ordered'));
    radio('ordered').checked = true;
    radio('ordered').dispatchEvent(new Event('change', { bubbles: true }));
    await fixture.whenStable();

    expect(session.mode()).toBe('ordered');
  });

  it('does not touch the drawing', async () => {
    session.resize({ width: 320, height: 320 });
    session.startStroke({ x: 10, y: 10, time: 0 });
    session.endStroke();
    const before = session.drawing();

    radio('ordered').click();
    await fixture.whenStable();

    expect(session.drawing()).toBe(before);
  });
});
