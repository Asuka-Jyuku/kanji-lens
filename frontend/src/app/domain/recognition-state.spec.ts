import type { RecognitionJob } from './recognition-job';
import { RecognitionError, isInProgress, stateOfError, stateOfJob } from './recognition-state';

const job = (overrides: Partial<RecognitionJob>): RecognitionJob => ({
  jobId: 'abc',
  status: 'queued',
  strokeOrderMode: 'unordered',
  ...overrides,
});

describe('recognition state', () => {
  it('shows a queued or processing job as waiting, with its id', () => {
    expect(stateOfJob(job({ status: 'queued' }))).toEqual({ phase: 'queued', jobId: 'abc' });
    expect(stateOfJob(job({ status: 'processing' }))).toEqual({
      phase: 'processing',
      jobId: 'abc',
    });
  });

  it('keeps the whole completed job, for the predictions', () => {
    const done = job({ status: 'completed', predictions: [{ kanji: '日', confidence: 0.6 }] });

    expect(stateOfJob(done)).toEqual({ phase: 'completed', job: done });
  });

  it('turns a failed job into its failure code', () => {
    expect(stateOfJob(job({ status: 'failed', failure: 'inference_failed' }))).toEqual({
      phase: 'failed',
      error: 'inference_failed',
    });
    expect(stateOfJob(job({ status: 'failed' }))).toEqual({ phase: 'failed', error: 'unexpected' });
  });

  it('turns a request error into its code, with the wait of a full queue', () => {
    expect(stateOfError(new RecognitionError('offline'))).toEqual({
      phase: 'failed',
      error: 'offline',
    });
    expect(stateOfError(new RecognitionError('queue_full', 5))).toEqual({
      phase: 'failed',
      error: 'queue_full',
      retryAfterSeconds: 5,
    });
  });

  it('treats anything but a RecognitionError as unexpected', () => {
    expect(stateOfError(new TypeError('boom'))).toEqual({ phase: 'failed', error: 'unexpected' });
  });

  it('is in progress from sending until a final state', () => {
    expect(isInProgress({ phase: 'idle' })).toBe(false);
    expect(isInProgress({ phase: 'sending' })).toBe(true);
    expect(isInProgress({ phase: 'queued', jobId: 'abc' })).toBe(true);
    expect(isInProgress({ phase: 'processing', jobId: 'abc' })).toBe(true);
    expect(isInProgress({ phase: 'completed', job: job({ status: 'completed' }) })).toBe(false);
    expect(isInProgress({ phase: 'failed', error: 'timeout' })).toBe(false);
  });
});
