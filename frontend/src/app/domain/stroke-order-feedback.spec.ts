import type { StrokeOrderEvaluation } from './recognition-job';
import { confidencePercent, strokeOrderFeedback } from './stroke-order-feedback';

const evaluated = (
  issues: Extract<StrokeOrderEvaluation, { status: 'evaluated' }>['issues'],
  drawnStrokes = 4,
  expectedStrokes = 4,
): StrokeOrderEvaluation => ({
  status: 'evaluated',
  correct: !issues.some((issue) => issue.type === 'order' || issue.type === 'direction'),
  expectedStrokes,
  drawnStrokes,
  issues,
});

describe('strokeOrderFeedback', () => {
  it('says the order is correct when nothing is out of order or reversed', () => {
    expect(strokeOrderFeedback(evaluated([]))).toEqual({
      verdict: 'correct',
      reason: null,
      mistakes: [],
      notes: [],
      strokeCount: null,
    });
  });

  it('lists the strokes out of order and the reversed ones, in the order they were drawn', () => {
    const feedback = strokeOrderFeedback(
      evaluated([
        { type: 'order', drawnStroke: 3, expectedPosition: 4 },
        { type: 'direction', drawnStroke: 2 },
        { type: 'order', drawnStroke: 4, expectedPosition: 3 },
      ]),
    );

    expect(feedback.verdict).toBe('mistakes');
    expect(feedback.mistakes.map((mistake) => [mistake.type, mistake.drawnStroke])).toEqual([
      ['direction', 2],
      ['order', 3],
      ['order', 4],
    ]);
  });

  it('notes joined and split strokes without calling them mistakes', () => {
    const joined = { type: 'joined', drawnStroke: 1, expectedStrokes: [1, 2] } as const;
    const broken = { type: 'broken', drawnStrokes: [3, 4], expectedStroke: 4 } as const;

    const feedback = strokeOrderFeedback(evaluated([joined, broken], 4, 4));

    expect(feedback.verdict).toBe('correct');
    expect(feedback.mistakes).toEqual([]);
    expect(feedback.notes).toEqual([joined, broken]);
  });

  it('says how many strokes were drawn when it differs from the kanji', () => {
    const feedback = strokeOrderFeedback(evaluated([], 3, 4));

    expect(feedback.strokeCount).toEqual({ drawn: 3, expected: 4 });
  });

  it.each(['stroke_count_mismatch', 'reference_missing'] as const)(
    'gives the reason when the order was not evaluated (%s)',
    (reason) => {
      expect(strokeOrderFeedback({ status: 'not_evaluated', reason })).toEqual({
        verdict: 'not_evaluated',
        reason,
        mistakes: [],
        notes: [],
        strokeCount: null,
      });
    },
  );
});

describe('confidencePercent', () => {
  it('rounds to a whole percentage', () => {
    expect([0.6, 0.255, 0.004, 1].map(confidencePercent)).toEqual([60, 26, 0, 100]);
  });
});
