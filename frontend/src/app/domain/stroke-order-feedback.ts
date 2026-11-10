import type {
  NotEvaluatedReason,
  StrokeOrderEvaluation,
  StrokeOrderIssue,
} from './recognition-job';

/** A mistake the student made: a stroke out of order or drawn the wrong way. */
export type StrokeOrderMistake = Extract<StrokeOrderIssue, { type: 'order' | 'direction' }>;

/** Strokes joined or split: noted, never counted as a mistake (ADR 0016). */
export type StrokeOrderNote = Extract<StrokeOrderIssue, { type: 'joined' | 'broken' }>;

/**
 * What the screen says about the stroke order of one candidate (docs/UI-UX.md, "Avaliação da
 * ordem em texto"). The template turns it into text through i18n (ADR 0009).
 */
export interface StrokeOrderFeedback {
  readonly verdict: 'correct' | 'mistakes' | 'not_evaluated';
  /** Only when not evaluated. */
  readonly reason: NotEvaluatedReason | null;
  /** In the order the strokes were drawn. */
  readonly mistakes: readonly StrokeOrderMistake[];
  readonly notes: readonly StrokeOrderNote[];
  /** Only when the student drew more or fewer strokes than the kanji has. */
  readonly strokeCount: { readonly drawn: number; readonly expected: number } | null;
}

export function strokeOrderFeedback(evaluation: StrokeOrderEvaluation): StrokeOrderFeedback {
  if (evaluation.status === 'not_evaluated') {
    return {
      verdict: 'not_evaluated',
      reason: evaluation.reason,
      mistakes: [],
      notes: [],
      strokeCount: null,
    };
  }
  const mistakes = evaluation.issues
    .filter((issue): issue is StrokeOrderMistake => isMistake(issue))
    .sort((a, b) => a.drawnStroke - b.drawnStroke);
  const notes = evaluation.issues.filter((issue): issue is StrokeOrderNote => !isMistake(issue));
  const { drawnStrokes: drawn, expectedStrokes: expected } = evaluation;
  return {
    // "correct" looks only at order and direction; joined or split strokes are fine.
    verdict: mistakes.length === 0 ? 'correct' : 'mistakes',
    reason: null,
    mistakes,
    notes,
    strokeCount: drawn === expected ? null : { drawn, expected },
  };
}

/** The confidence as a whole percentage, as the screen shows it ("81%", Nielsen 2). */
export function confidencePercent(confidence: number): number {
  return Math.round(confidence * 100);
}

function isMistake(issue: StrokeOrderIssue): boolean {
  return issue.type === 'order' || issue.type === 'direction';
}
