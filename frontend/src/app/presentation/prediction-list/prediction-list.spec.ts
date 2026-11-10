import { signal } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';

import { RecognizeDrawing } from '../../application/recognize-drawing.use-case';
import type { RecognitionJob } from '../../domain/recognition-job';
import { PredictionList } from './prediction-list';

const UNORDERED: RecognitionJob = {
  jobId: 'a',
  status: 'completed',
  strokeOrderMode: 'unordered',
  predictions: [
    { kanji: '日', confidence: 0.6 },
    { kanji: '目', confidence: 0.25 },
  ],
};

const ORDERED: RecognitionJob = {
  jobId: 'b',
  status: 'completed',
  strokeOrderMode: 'ordered',
  predictions: [
    {
      kanji: '日',
      confidence: 0.6,
      strokeOrder: {
        status: 'evaluated',
        correct: false,
        expectedStrokes: 4,
        drawnStrokes: 4,
        issues: [
          { type: 'order', drawnStroke: 3, expectedPosition: 4 },
          { type: 'direction', drawnStroke: 2 },
        ],
      },
    },
    {
      kanji: '目',
      confidence: 0.25,
      strokeOrder: {
        status: 'evaluated',
        correct: true,
        expectedStrokes: 5,
        drawnStrokes: 4,
        issues: [],
      },
    },
    {
      kanji: '白',
      confidence: 0.1,
      strokeOrder: { status: 'not_evaluated', reason: 'reference_missing' },
    },
  ],
};

describe('PredictionList', () => {
  let fixture: ComponentFixture<PredictionList>;
  let page: HTMLElement;
  const result = signal<RecognitionJob | null>(null);

  beforeEach(async () => {
    result.set(null);
    await TestBed.configureTestingModule({
      imports: [PredictionList],
      providers: [{ provide: RecognizeDrawing, useValue: { result } }],
    }).compileComponents();
    fixture = TestBed.createComponent(PredictionList);
    page = fixture.nativeElement as HTMLElement;
    await fixture.whenStable();
  });

  async function show(job: RecognitionJob | null) {
    result.set(job);
    await fixture.whenStable();
  }

  const text = (selector: string) =>
    Array.from(page.querySelectorAll(selector)).map((each) =>
      each.textContent?.replace(/\s+/g, ' ').trim(),
    );

  it('shows nothing before a result', () => {
    expect(page.querySelector('.predictions')).toBeNull();
    expect(page.querySelector('[role="status"]')?.textContent?.trim()).toBe('');
  });

  it('lists the candidates best first, in Japanese, with the confidence in percent', async () => {
    await show(UNORDERED);

    expect(text('.candidate')).toEqual(['日60%', '目25%']);
    expect(page.querySelector('.kanji')?.getAttribute('lang')).toBe('ja');
  });

  it('has nothing to pick when the stroke order does not matter', async () => {
    await show(UNORDERED);

    expect(page.querySelector('button')).toBeNull();
    expect(page.querySelector('[role="status"]')?.textContent?.trim()).toBe('');
  });

  it('says, for the best candidate, which strokes to fix', async () => {
    await show(ORDERED);

    const buttons = page.querySelectorAll('button.candidate');
    expect(buttons[0].getAttribute('aria-pressed')).toBe('true');
    expect(text('[role="status"] .verdict')).toEqual([
      'Ordem dos traços de 日, com o que corrigir:',
    ]);
    expect(text('[role="status"] li')).toEqual([
      '2º traço: direção invertida.',
      '3º traço: deveria ser o 4º.',
    ]);
  });

  it('shows the stroke order of the candidate the student picks', async () => {
    await show(ORDERED);

    (page.querySelectorAll('button.candidate')[1] as HTMLButtonElement).click();
    await fixture.whenStable();

    expect(page.querySelectorAll('button.candidate')[1].getAttribute('aria-pressed')).toBe('true');
    expect(text('[role="status"] .verdict')).toEqual(['Ordem dos traços certa para 目.']);
    expect(text('[role="status"] li')).toEqual(['Você fez 4 traços; o kanji tem 5.']);
  });

  it('says why a candidate was not evaluated', async () => {
    await show(ORDERED);

    (page.querySelectorAll('button.candidate')[2] as HTMLButtonElement).click();
    await fixture.whenStable();

    expect(text('[role="status"] .verdict')).toEqual([
      'Não deu para avaliar a ordem de 白: ele não está na referência de traços.',
    ]);
  });

  it('goes back to the best candidate when a new result arrives', async () => {
    await show(ORDERED);
    (page.querySelectorAll('button.candidate')[1] as HTMLButtonElement).click();
    await fixture.whenStable();

    await show({ ...ORDERED, jobId: 'c', predictions: [...(ORDERED.predictions ?? [])] });

    expect(page.querySelectorAll('button.candidate')[0].getAttribute('aria-pressed')).toBe('true');
  });
});
