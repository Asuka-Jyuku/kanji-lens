/**
 * A recognition job as the API reports it (ARCHITECTURE.md, section 2.2; ADR 0016): the same
 * state comes from GET /api/recognitions/{id} and from each SSE event (ADR 0020). What does not
 * apply is absent: no predictions before `completed`, no stroke order in the `unordered` mode,
 * and the failure only in a `failed` job.
 */
import type { StrokeOrderMode } from './stroke-order-mode';

export const JOB_STATUSES = ['queued', 'processing', 'completed', 'failed'] as const;

/** queued -> processing -> completed | failed (docs/architecture/domain.md). */
export type JobStatus = (typeof JOB_STATUSES)[number];

/** Why a job failed; a code the screen translates (ADR 0009). */
export type JobFailure = 'inference_failed';

export type NotEvaluatedReason = 'stroke_count_mismatch' | 'reference_missing';

/** Strokes are numbered from 1, in the order they were drawn or are expected. */
export type StrokeOrderIssue =
  | { readonly type: 'order'; readonly drawnStroke: number; readonly expectedPosition: number }
  | { readonly type: 'direction'; readonly drawnStroke: number }
  | {
      readonly type: 'joined';
      readonly drawnStroke: number;
      readonly expectedStrokes: readonly number[];
    }
  | {
      readonly type: 'broken';
      readonly drawnStrokes: readonly number[];
      readonly expectedStroke: number;
    };

export type StrokeOrderEvaluation =
  | {
      readonly status: 'evaluated';
      readonly correct: boolean;
      readonly expectedStrokes: number;
      readonly drawnStrokes: number;
      readonly issues: readonly StrokeOrderIssue[];
    }
  | { readonly status: 'not_evaluated'; readonly reason: NotEvaluatedReason };

export interface Prediction {
  /** One character; shown with lang="ja" (ADR 0009). */
  readonly kanji: string;
  /** From 0 to 1. */
  readonly confidence: number;
  /** Only in the `ordered` mode. */
  readonly strokeOrder?: StrokeOrderEvaluation;
}

export interface RecognitionJob {
  readonly jobId: string;
  readonly status: JobStatus;
  readonly strokeOrderMode: StrokeOrderMode;
  /** Only when `completed`, best first. */
  readonly predictions?: readonly Prediction[];
  /** Only when `failed`. */
  readonly failure?: JobFailure;
}

/** The job as POST /api/recognitions answers it: its id and first status. */
export interface SubmittedJob {
  readonly jobId: string;
  readonly status: JobStatus;
}

/** `completed` and `failed` are final: the job changes no more. */
export function isFinalStatus(status: JobStatus): boolean {
  return status === 'completed' || status === 'failed';
}
