import type { RecognitionJob } from '../domain/recognition-job';
import { SseResultStream } from './sse-result-stream';

/** A stand-in for the browser's EventSource (jsdom has none), driven by the test. */
class FakeEventSource extends EventTarget {
  static readonly CONNECTING = 0;
  static readonly OPEN = 1;
  static readonly CLOSED = 2;
  static readonly created: FakeEventSource[] = [];

  readyState = FakeEventSource.CONNECTING;
  closed = false;

  constructor(readonly url: string) {
    super();
    FakeEventSource.created.push(this);
  }

  close(): void {
    this.closed = true;
    this.readyState = FakeEventSource.CLOSED;
  }

  /** An event as the API sends it: named after the state, the full state as data. */
  emit(event: string, data: unknown): void {
    this.dispatchEvent(new MessageEvent(event, { data: JSON.stringify(data) }));
  }

  fail(readyState: number): void {
    this.readyState = readyState;
    this.dispatchEvent(new Event('error'));
  }
}

const body = (status: string) => ({
  job_id: 'abc123',
  status,
  stroke_order_mode: 'unordered',
  ...(status === 'completed' ? { predictions: [{ kanji: '日', confidence: 0.6 }] } : {}),
});

describe('SseResultStream', () => {
  let states: RecognitionJob[];
  let errors: boolean[];

  beforeEach(() => {
    FakeEventSource.created.length = 0;
    vi.stubGlobal('EventSource', FakeEventSource);
    states = [];
    errors = [];
  });

  afterEach(() => vi.unstubAllGlobals());

  function open() {
    const connection = new SseResultStream().open('abc123', {
      state: (job) => states.push(job),
      error: (closed) => errors.push(closed),
    });
    return { connection, source: FakeEventSource.created[0] };
  }

  it('listens to the job events at the relative /api URL', () => {
    const { source } = open();

    expect(source.url).toBe('/api/recognitions/abc123/events');
  });

  it('passes on each state, in the domain shape', () => {
    const { source } = open();

    source.emit('queued', body('queued'));
    source.emit('processing', body('processing'));

    expect(states).toEqual([
      { jobId: 'abc123', status: 'queued', strokeOrderMode: 'unordered' },
      { jobId: 'abc123', status: 'processing', strokeOrderMode: 'unordered' },
    ]);
    expect(source.closed).toBe(false);
  });

  it('closes at the final state, before the end of the stream makes it reconnect', () => {
    const { source } = open();

    source.emit('completed', body('completed'));
    source.fail(FakeEventSource.CONNECTING);

    expect(states.map((job) => job.status)).toEqual(['completed']);
    expect(source.closed).toBe(true);
    expect(errors).toEqual([]);
  });

  it('closes at a failed job too', () => {
    const { source } = open();

    source.emit('failed', { ...body('failed'), failure: 'inference_failed' });

    expect(states[0].failure).toBe('inference_failed');
    expect(source.closed).toBe(true);
  });

  it('reports a dropped connection it is retrying, and one the browser gave up on', () => {
    const { source } = open();

    source.fail(FakeEventSource.CONNECTING);
    source.fail(FakeEventSource.CLOSED);

    expect(errors).toEqual([false, true]);
  });

  it('gives up on an event it cannot read', () => {
    const { source } = open();

    source.emit('completed', { job_id: 'abc123', status: 'done' });

    expect(states).toEqual([]);
    expect(errors).toEqual([true]);
    expect(source.closed).toBe(true);
  });

  it('stops when the use case closes it, and reports nothing after that', () => {
    const { connection, source } = open();

    connection.close();
    source.emit('completed', body('completed'));
    source.fail(FakeEventSource.CLOSED);

    expect(source.closed).toBe(true);
    expect(states).toEqual([]);
    expect(errors).toEqual([]);
  });
});
