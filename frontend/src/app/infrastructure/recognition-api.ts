/**
 * The recognition API's JSON, read into the domain (ARCHITECTURE.md, sections 2.2 and 5.3).
 * Shared by the HTTP gateway and the SSE stream, so both paths read the job the same way
 * (ADR 0020, "Dois caminhos para o mesmo dado"). An answer that does not fit is refused with
 * the `unexpected` code instead of reaching the screen half-read.
 */
import {
  JOB_STATUSES,
  JobStatus,
  Prediction,
  RecognitionJob,
  StrokeOrderEvaluation,
  StrokeOrderIssue,
  SubmittedJob,
} from '../domain/recognition-job';
import { RecognitionError } from '../domain/recognition-state';
import { isStrokeOrderMode } from '../domain/stroke-order-mode';

/** Relative, so the phone reaches the API through the page's own server (ADR 0007). */
export const RECOGNITIONS_URL = '/api/recognitions';

export function recognitionUrl(jobId: string): string {
  return `${RECOGNITIONS_URL}/${encodeURIComponent(jobId)}`;
}

type Json = Record<string, unknown>;

/** The body of a 202 from POST /api/recognitions. */
export function readSubmittedJob(body: unknown): SubmittedJob {
  const json = object(body);
  return { jobId: text(json['job_id']), status: status(json['status']) };
}

/** The job's state, from GET /api/recognitions/{id} or from an SSE event's data. */
export function readRecognitionJob(body: unknown): RecognitionJob {
  const json = object(body);
  const mode = json['stroke_order_mode'];
  if (!isStrokeOrderMode(mode)) {
    bad();
  }
  const job: RecognitionJob = {
    jobId: text(json['job_id']),
    status: status(json['status']),
    strokeOrderMode: mode,
  };
  const predictions = json['predictions'];
  const failure = json['failure'];
  return {
    ...job,
    ...(predictions === undefined ? {} : { predictions: list(predictions).map(prediction) }),
    ...(failure === undefined ? {} : { failure: failure === 'inference_failed' ? failure : bad() }),
  };
}

function prediction(value: unknown): Prediction {
  const json = object(value);
  const strokeOrder = json['stroke_order'];
  return {
    kanji: text(json['kanji']),
    confidence: count(json['confidence']),
    ...(strokeOrder === undefined ? {} : { strokeOrder: evaluation(strokeOrder) }),
  };
}

function evaluation(value: unknown): StrokeOrderEvaluation {
  const json = object(value);
  if (json['status'] === 'not_evaluated') {
    const reason = json['reason'];
    if (reason !== 'stroke_count_mismatch' && reason !== 'reference_missing') {
      bad();
    }
    return { status: 'not_evaluated', reason };
  }
  if (json['status'] !== 'evaluated' || typeof json['correct'] !== 'boolean') {
    bad();
  }
  return {
    status: 'evaluated',
    correct: json['correct'],
    expectedStrokes: count(json['expected_strokes']),
    drawnStrokes: count(json['drawn_strokes']),
    issues: list(json['issues']).map(issue),
  };
}

function issue(value: unknown): StrokeOrderIssue {
  const json = object(value);
  switch (json['type']) {
    case 'order':
      return {
        type: 'order',
        drawnStroke: count(json['drawn_stroke']),
        expectedPosition: count(json['expected_position']),
      };
    case 'direction':
      return { type: 'direction', drawnStroke: count(json['drawn_stroke']) };
    case 'joined':
      return {
        type: 'joined',
        drawnStroke: count(json['drawn_stroke']),
        expectedStrokes: list(json['expected_strokes']).map(count),
      };
    case 'broken':
      return {
        type: 'broken',
        drawnStrokes: list(json['drawn_strokes']).map(count),
        expectedStroke: count(json['expected_stroke']),
      };
    default:
      bad();
  }
}

function status(value: unknown): JobStatus {
  return (JOB_STATUSES as readonly unknown[]).includes(value) ? (value as JobStatus) : bad();
}

function object(value: unknown): Json {
  return typeof value === 'object' && value !== null && !Array.isArray(value)
    ? (value as Json)
    : bad();
}

function list(value: unknown): unknown[] {
  return Array.isArray(value) ? value : bad();
}

function text(value: unknown): string {
  return typeof value === 'string' && value !== '' ? value : bad();
}

function count(value: unknown): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : bad();
}

function bad(): never {
  throw new RecognitionError('unexpected');
}
