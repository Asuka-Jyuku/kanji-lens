import { Drawing } from './drawing';
import {
  DrawingLabel,
  STROKE_ORDER_LABELS,
  drawingSample,
  isSingleKanji,
  isStrokeOrderLabel,
  parseStrokeNumbers,
  sampleFileName,
  serializeSample,
} from './drawing-sample';

const DRAWING: Drawing = {
  canvas: { width: 320, height: 320 },
  strokes: [
    [
      { x: 10, y: 10, t: 0 },
      { x: 10, y: 90, t: 120 },
    ],
    [{ x: 50, y: 50, t: 400 }],
  ],
};
const AT = new Date(Date.UTC(2026, 10, 10, 15, 30, 45, 123));

describe('drawing sample', () => {
  it('puts the API body, unchanged, next to the answer key and the format', () => {
    const label: DrawingLabel = { kanji: '日', stroke_order: 'order', strokes: [2] };

    expect(drawingSample(DRAWING, 'ordered', label, AT)).toEqual({
      format: 'kanjilens-drawing',
      version: 1,
      exported_at: '2026-11-10T15:30:45.123Z',
      label: { kanji: '日', stroke_order: 'order', strokes: [2] },
      request: {
        stroke_order_mode: 'ordered',
        canvas: { width: 320, height: 320 },
        strokes: [
          [
            [10, 10, 0],
            [10, 90, 120],
          ],
          [[50, 50, 400]],
        ],
      },
    });
  });

  it('points at no stroke when the order is right', () => {
    const sample = drawingSample(
      DRAWING,
      'ordered',
      { kanji: '日', stroke_order: 'correct', strokes: [1] },
      AT,
    );

    expect(sample.label.strokes).toEqual([]);
  });

  it('writes one point per line, and reads back as the same sample', () => {
    const sample = drawingSample(
      { canvas: { width: 320, height: 320 }, strokes: [[{ x: -1.5, y: 2e-7, t: 0 }]] },
      'ordered',
      { kanji: '一', stroke_order: 'joined', strokes: [1, 2] },
      AT,
    );

    const text = serializeSample(sample);

    expect(text).toContain('"strokes": [1, 2]');
    expect(text).toContain('[-1.5, 2e-7, 0]');
    expect(text.endsWith('}\n')).toBe(true);
    expect(JSON.parse(text)).toEqual(sample);
  });

  it('names the file in ASCII by kanji, mistake and time', () => {
    const sample = drawingSample(
      DRAWING,
      'unordered',
      { kanji: '日', stroke_order: 'direction', strokes: [] },
      AT,
    );

    expect(sampleFileName(sample)).toBe('u65e5-direction-20261110T153045Z.json');
  });

  it('takes one kanji, and nothing else, as the key', () => {
    expect(isSingleKanji('日')).toBe(true);
    expect(isSingleKanji('𠮟')).toBe(true);
    expect(isSingleKanji('')).toBe(false);
    expect(isSingleKanji('日本')).toBe(false);
    expect(isSingleKanji('あ')).toBe(false);
    expect(isSingleKanji('a')).toBe(false);
  });

  it('reads stroke numbers typed with commas or spaces, sorted and without repeats', () => {
    expect(parseStrokeNumbers('4, 3', 5)).toEqual([3, 4]);
    expect(parseStrokeNumbers(' 2 2,5 ', 5)).toEqual([2, 5]);
    expect(parseStrokeNumbers('', 5)).toEqual([]);
  });

  it('refuses a stroke number that is not a stroke of the drawing', () => {
    expect(parseStrokeNumbers('0', 5)).toBeNull();
    expect(parseStrokeNumbers('6', 5)).toBeNull();
    expect(parseStrokeNumbers('1.5', 5)).toBeNull();
    expect(parseStrokeNumbers('dois', 5)).toBeNull();
  });

  it('knows the stroke order labels, the ADR 0016 mistakes plus a stroke too many or few', () => {
    expect(STROKE_ORDER_LABELS).toEqual([
      'correct',
      'order',
      'direction',
      'joined',
      'broken',
      'extra',
      'missing',
    ]);
    expect(isStrokeOrderLabel('joined')).toBe(true);
    expect(isStrokeOrderLabel('swapped')).toBe(false);
  });
});
