/**
 * What the screen shows about the recognition: nothing yet, the drawing on its way, the job in
 * the queue or being recognized, the result, or what went wrong and what to do (docs/UI-UX.md,
 * "O estado do job sempre visível"; Nielsen 1, WCAG 4.1.3 and 3.3.1).
 */
import type { RecognitionJob } from './recognition-job';

/**
 * Why a recognition did not end in a result. The API's codes (ARCHITECTURE.md, section 5.3),
 * the job's failure, and what only the client sees: no connection, no answer in time, or an
 * answer it cannot read. The screen turns each one into a message (ADR 0009).
 */
export type RecognitionErrorCode =
  | 'queue_full'
  | 'inference_failed'
  | 'invalid_drawing'
  | 'drawing_too_large'
  | 'job_not_found'
  | 'offline'
  | 'timeout'
  | 'unexpected';

/** A failed request or job, with the seconds to wait when the queue is full. */
export class RecognitionError extends Error {
  constructor(
    readonly code: RecognitionErrorCode,
    readonly retryAfterSeconds?: number,
  ) {
    super(code);
    this.name = 'RecognitionError';
  }
}

export type RecognitionState =
  | { readonly phase: 'idle' }
  | { readonly phase: 'sending' }
  | { readonly phase: 'queued' | 'processing'; readonly jobId: string }
  | { readonly phase: 'completed'; readonly job: RecognitionJob }
  | {
      readonly phase: 'failed';
      readonly error: RecognitionErrorCode;
      readonly retryAfterSeconds?: number;
    };

export const IDLE: RecognitionState = { phase: 'idle' };

/** The state a job's status puts the screen in. */
export function stateOfJob(job: RecognitionJob): RecognitionState {
  switch (job.status) {
    case 'queued':
    case 'processing':
      return { phase: job.status, jobId: job.jobId };
    case 'completed':
      return { phase: 'completed', job };
    case 'failed':
      return { phase: 'failed', error: job.failure ?? 'unexpected' };
  }
}

/** The state a failed request puts the screen in; anything but a RecognitionError is a bug. */
export function stateOfError(error: unknown): RecognitionState {
  if (!(error instanceof RecognitionError)) {
    return { phase: 'failed', error: 'unexpected' };
  }
  return error.retryAfterSeconds === undefined
    ? { phase: 'failed', error: error.code }
    : { phase: 'failed', error: error.code, retryAfterSeconds: error.retryAfterSeconds };
}

/** True while a recognition is under way: sent and not yet final. */
export function isInProgress(state: RecognitionState): boolean {
  return state.phase === 'sending' || state.phase === 'queued' || state.phase === 'processing';
}
