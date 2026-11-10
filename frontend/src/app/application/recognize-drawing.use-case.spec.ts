import { TestBed } from '@angular/core/testing';

import type { RecognitionJob, SubmittedJob } from '../domain/recognition-job';
import type { RecognitionRequest } from '../domain/recognition-request';
import { RecognitionError } from '../domain/recognition-state';
import { DrawingSession } from './drawing-session';
import { RecognitionGateway } from './recognition.gateway';
import { FOLLOW_POLICY, RecognizeDrawing } from './recognize-drawing.use-case';
import { ResultStream, ResultStreamConnection, ResultStreamHandlers } from './result-stream';

/** The API, answering what each test tells it to. */
class FakeGateway extends RecognitionGateway {
  readonly sent: RecognitionRequest[] = [];
  submitAnswer: () => Promise<SubmittedJob> = async () => ({ jobId: 'job-1', status: 'queued' });
  /** One answer per GET, in order; the last one repeats. */
  getAnswers: (() => Promise<RecognitionJob>)[] = [];
  gets = 0;

  submit(request: RecognitionRequest): Promise<SubmittedJob> {
    this.sent.push(request);
    return this.submitAnswer();
  }

  get(): Promise<RecognitionJob> {
    const answer = this.getAnswers[Math.min(this.gets, this.getAnswers.length - 1)];
    this.gets += 1;
    return answer();
  }
}

/** The SSE stream, pushed by hand. */
class FakeStream extends ResultStream {
  readonly opened: { jobId: string; handlers: ResultStreamHandlers; closed: boolean }[] = [];

  open(jobId: string, handlers: ResultStreamHandlers): ResultStreamConnection {
    const entry = { jobId, handlers, closed: false };
    this.opened.push(entry);
    return { close: () => (entry.closed = true) };
  }

  get last() {
    return this.opened[this.opened.length - 1];
  }
}

const job = (status: RecognitionJob['status'], extra: Partial<RecognitionJob> = {}) =>
  ({ jobId: 'job-1', status, strokeOrderMode: 'unordered', ...extra }) as RecognitionJob;
const completed = job('completed', { predictions: [{ kanji: '日', confidence: 0.6 }] });

/** Lets pending promises (the fake API's answers) settle, moving the clock by `ms`. */
const settle = (ms = 0) => vi.advanceTimersByTimeAsync(ms);

describe('RecognizeDrawing', () => {
  let gateway: FakeGateway;
  let stream: FakeStream;
  let recognition: RecognizeDrawing;
  let session: DrawingSession;

  beforeEach(() => {
    vi.useFakeTimers();
    gateway = new FakeGateway();
    stream = new FakeStream();
    TestBed.configureTestingModule({
      providers: [
        { provide: RecognitionGateway, useValue: gateway },
        { provide: ResultStream, useValue: stream },
      ],
    });
    recognition = TestBed.inject(RecognizeDrawing);
    session = TestBed.inject(DrawingSession);
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  function draw(): void {
    session.resize({ width: 320, height: 320 });
    session.startStroke({ x: 10, y: 10, time: 100 });
    session.extendStroke({ x: 60, y: 80, time: 116 });
    session.endStroke();
  }

  async function sendAndQueue(): Promise<void> {
    draw();
    await recognition.recognize();
  }

  it('does not send an empty canvas', async () => {
    expect(recognition.canRecognize()).toBe(false);

    await recognition.recognize();

    expect(gateway.sent).toEqual([]);
    expect(recognition.state()).toEqual({ phase: 'idle' });
  });

  it('sends the drawing as drawn, with the chosen mode', async () => {
    TestBed.inject(DrawingSession).chooseMode('ordered');

    await sendAndQueue();

    expect(gateway.sent).toEqual([
      {
        stroke_order_mode: 'ordered',
        canvas: { width: 320, height: 320 },
        strokes: [
          [
            [10, 10, 0],
            [60, 80, 16],
          ],
        ],
      },
    ]);
  });

  it('goes sending -> queued -> processing -> completed, following the stream', async () => {
    let answer!: (job: SubmittedJob) => void;
    gateway.submitAnswer = () => new Promise((resolve) => (answer = resolve));
    draw();

    const sending = recognition.recognize();
    expect(recognition.state()).toEqual({ phase: 'sending' });

    answer({ jobId: 'job-1', status: 'queued' });
    await sending;
    expect(recognition.state()).toEqual({ phase: 'queued', jobId: 'job-1' });
    expect(stream.last.jobId).toBe('job-1');

    stream.last.handlers.state(job('processing'));
    expect(recognition.state()).toEqual({ phase: 'processing', jobId: 'job-1' });

    stream.last.handlers.state(completed);
    expect(recognition.state()).toEqual({ phase: 'completed', job: completed });
    expect(recognition.result()).toEqual(completed);
    expect(stream.last.closed).toBe(true);
  });

  it('keeps "Reconhecer" off while a job is under way, and on again at the end', async () => {
    await sendAndQueue();
    expect(recognition.canRecognize()).toBe(false);

    await recognition.recognize();
    expect(gateway.sent).toHaveLength(1);

    stream.last.handlers.state(completed);
    expect(recognition.canRecognize()).toBe(true);
  });

  it('says the recognition failed when the job fails', async () => {
    await sendAndQueue();

    stream.last.handlers.state(job('failed', { failure: 'inference_failed' }));

    expect(recognition.state()).toEqual({ phase: 'failed', error: 'inference_failed' });
    expect(recognition.canRecognize()).toBe(true);
  });

  it.each(['invalid_drawing', 'drawing_too_large', 'offline', 'unexpected'] as const)(
    'tells the %s error from sending, and lets the user try again',
    async (code) => {
      gateway.submitAnswer = () => Promise.reject(new RecognitionError(code));

      await sendAndQueue();

      expect(recognition.state()).toEqual({ phase: 'failed', error: code });
      expect(recognition.canRecognize()).toBe(true);
      expect(stream.opened).toEqual([]);
    },
  );

  it('waits the Retry-After of a full queue before "Reconhecer" is on again', async () => {
    gateway.submitAnswer = () => Promise.reject(new RecognitionError('queue_full', 5));

    await sendAndQueue();

    expect(recognition.state()).toEqual({
      phase: 'failed',
      error: 'queue_full',
      retryAfterSeconds: 5,
    });
    expect(recognition.canRecognize()).toBe(false);
    await settle(4_999);
    expect(recognition.canRecognize()).toBe(false);
    await settle(1);
    expect(recognition.canRecognize()).toBe(true);
  });

  describe('when the stream fails', () => {
    it('keeps the stream through errors short of the limit', async () => {
      await sendAndQueue();

      for (let i = 1; i < FOLLOW_POLICY.streamErrorsBeforePolling; i++) {
        stream.last.handlers.error(false);
      }
      stream.last.handlers.state(job('processing'));
      stream.last.handlers.error(false);

      expect(stream.last.closed).toBe(false);
      expect(gateway.gets).toBe(0);
    });

    it('switches to polling after repeated errors, until a final state', async () => {
      gateway.getAnswers = [async () => job('processing'), async () => completed];
      await sendAndQueue();

      for (let i = 0; i < FOLLOW_POLICY.streamErrorsBeforePolling; i++) {
        stream.last.handlers.error(false);
      }
      await settle();

      expect(stream.last.closed).toBe(true);
      expect(gateway.gets).toBe(1);
      expect(recognition.state()).toEqual({ phase: 'processing', jobId: 'job-1' });

      await settle(FOLLOW_POLICY.pollIntervalMs);
      expect(gateway.gets).toBe(2);
      expect(recognition.state()).toEqual({ phase: 'completed', job: completed });

      await settle(FOLLOW_POLICY.pollIntervalMs * 5);
      expect(gateway.gets).toBe(2);
    });

    it('polls at once when the stream gives up by itself (a 404, an unreadable event)', async () => {
      gateway.getAnswers = [() => Promise.reject(new RecognitionError('job_not_found'))];
      await sendAndQueue();

      stream.last.handlers.error(true);
      await settle();

      expect(gateway.gets).toBe(1);
      expect(recognition.state()).toEqual({ phase: 'failed', error: 'job_not_found' });
    });

    it('rides out a lost poll or two, and says so after the limit', async () => {
      const offline = () => Promise.reject(new RecognitionError('offline'));
      gateway.getAnswers = [offline, offline, async () => job('processing'), offline];
      await sendAndQueue();
      stream.last.handlers.error(true);
      await settle();
      await settle(FOLLOW_POLICY.pollIntervalMs * 2);

      expect(recognition.state()).toEqual({ phase: 'processing', jobId: 'job-1' });

      await settle(FOLLOW_POLICY.pollIntervalMs * FOLLOW_POLICY.pollErrorsBeforeGivingUp);
      expect(recognition.state()).toEqual({ phase: 'failed', error: 'offline' });
      const polls = gateway.gets;
      await settle(FOLLOW_POLICY.pollIntervalMs * 5);
      expect(gateway.gets).toBe(polls);
    });
  });

  it('gives up when no final state comes in time, and ignores the stream after that', async () => {
    await sendAndQueue();
    const first = stream.last;

    await settle(FOLLOW_POLICY.jobTimeoutMs);

    expect(recognition.state()).toEqual({ phase: 'failed', error: 'timeout' });
    expect(first.closed).toBe(true);
    first.handlers.state(completed);
    expect(recognition.state()).toEqual({ phase: 'failed', error: 'timeout' });
  });

  it('closes the stream and stops polling when the app goes away', async () => {
    gateway.getAnswers = [async () => job('processing')];
    await sendAndQueue();
    const first = stream.last;

    TestBed.resetTestingModule();

    expect(first.closed).toBe(true);
    await settle(FOLLOW_POLICY.jobTimeoutMs);
    expect(gateway.gets).toBe(0);
  });

  it('follows only the new job after a new recognition', async () => {
    await sendAndQueue();
    const first = stream.last;
    first.handlers.state(job('failed', { failure: 'inference_failed' }));

    gateway.submitAnswer = async () => ({ jobId: 'job-2', status: 'queued' });
    await recognition.recognize();
    first.handlers.state(completed);

    expect(stream.last.jobId).toBe('job-2');
    expect(recognition.state()).toEqual({ phase: 'queued', jobId: 'job-2' });
  });
});
