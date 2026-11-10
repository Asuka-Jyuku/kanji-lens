import { RecognitionError } from '../domain/recognition-state';
import { readRecognitionJob, readSubmittedJob, recognitionUrl } from './recognition-api';

// The bodies as the backend sends them (recognition_state.py; ARCHITECTURE.md, section 2.2).
const ORDERED_COMPLETED = {
  job_id: 'abc123',
  status: 'completed',
  stroke_order_mode: 'ordered',
  predictions: [
    {
      kanji: '日',
      confidence: 0.81,
      stroke_order: {
        status: 'evaluated',
        correct: false,
        expected_strokes: 4,
        drawn_strokes: 4,
        issues: [
          { type: 'order', drawn_stroke: 3, expected_position: 2 },
          { type: 'direction', drawn_stroke: 4 },
          { type: 'joined', drawn_stroke: 1, expected_strokes: [1, 2] },
          { type: 'broken', drawn_strokes: [2, 3], expected_stroke: 3 },
        ],
      },
    },
    {
      kanji: '目',
      confidence: 0.12,
      stroke_order: { status: 'not_evaluated', reason: 'stroke_count_mismatch' },
    },
  ],
};

function refused(read: () => unknown): RecognitionError {
  try {
    read();
  } catch (error) {
    return error as RecognitionError;
  }
  throw new Error('expected the body to be refused');
}

describe('recognition API bodies', () => {
  it('reads the answer to a POST', () => {
    expect(readSubmittedJob({ job_id: 'abc123', status: 'queued' })).toEqual({
      jobId: 'abc123',
      status: 'queued',
    });
  });

  it('reads a waiting job, with nothing that does not apply yet', () => {
    expect(
      readRecognitionJob({
        job_id: 'abc123',
        status: 'processing',
        stroke_order_mode: 'unordered',
      }),
    ).toEqual({ jobId: 'abc123', status: 'processing', strokeOrderMode: 'unordered' });
  });

  it('reads a completed ordered job, with the stroke order of each candidate', () => {
    expect(readRecognitionJob(ORDERED_COMPLETED)).toEqual({
      jobId: 'abc123',
      status: 'completed',
      strokeOrderMode: 'ordered',
      predictions: [
        {
          kanji: '日',
          confidence: 0.81,
          strokeOrder: {
            status: 'evaluated',
            correct: false,
            expectedStrokes: 4,
            drawnStrokes: 4,
            issues: [
              { type: 'order', drawnStroke: 3, expectedPosition: 2 },
              { type: 'direction', drawnStroke: 4 },
              { type: 'joined', drawnStroke: 1, expectedStrokes: [1, 2] },
              { type: 'broken', drawnStrokes: [2, 3], expectedStroke: 3 },
            ],
          },
        },
        {
          kanji: '目',
          confidence: 0.12,
          strokeOrder: { status: 'not_evaluated', reason: 'stroke_count_mismatch' },
        },
      ],
    });
  });

  it('reads a failed job with its failure code', () => {
    expect(
      readRecognitionJob({
        job_id: 'abc123',
        status: 'failed',
        stroke_order_mode: 'ordered',
        failure: 'inference_failed',
      }),
    ).toEqual({
      jobId: 'abc123',
      status: 'failed',
      strokeOrderMode: 'ordered',
      failure: 'inference_failed',
    });
  });

  it.each([
    ['not an object', 'completed'],
    ['an unknown status', { job_id: 'a', status: 'done', stroke_order_mode: 'ordered' }],
    ['an unknown mode', { job_id: 'a', status: 'queued', stroke_order_mode: 'strict' }],
    ['no job id', { status: 'queued', stroke_order_mode: 'ordered' }],
    ['an unknown failure', { ...ORDERED_COMPLETED, status: 'failed', failure: 'boom' }],
    ['predictions that are not a list', { ...ORDERED_COMPLETED, predictions: {} }],
    [
      'an unknown issue',
      {
        ...ORDERED_COMPLETED,
        predictions: [
          {
            kanji: '日',
            confidence: 0.8,
            stroke_order: {
              status: 'evaluated',
              correct: false,
              expected_strokes: 4,
              drawn_strokes: 4,
              issues: [{ type: 'speed' }],
            },
          },
        ],
      },
    ],
  ])('refuses a body with %s as unexpected', (_, body) => {
    const error = refused(() => readRecognitionJob(body));

    expect(error).toBeInstanceOf(RecognitionError);
    expect(error.code).toBe('unexpected');
  });

  it('puts the job id in the path safely', () => {
    expect(recognitionUrl('a/b?c')).toBe('/api/recognitions/a%2Fb%3Fc');
  });
});
