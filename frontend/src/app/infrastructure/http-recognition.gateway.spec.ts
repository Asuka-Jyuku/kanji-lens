import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';

import { RecognitionError } from '../domain/recognition-state';
import { DEFAULT_RETRY_AFTER_SECONDS, HttpRecognitionGateway } from './http-recognition.gateway';

const REQUEST = {
  stroke_order_mode: 'unordered' as const,
  canvas: { width: 320, height: 320 },
  strokes: [[[10, 10, 0] as [number, number, number]]],
};

describe('HttpRecognitionGateway', () => {
  let gateway: HttpRecognitionGateway;
  let backend: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting(), HttpRecognitionGateway],
    });
    gateway = TestBed.inject(HttpRecognitionGateway);
    backend = TestBed.inject(HttpTestingController);
  });

  afterEach(() => backend.verify());

  /** Starts the call, answers it with `respond`, and returns what the gateway made of it. */
  async function submitAnswered(
    respond: (request: ReturnType<HttpTestingController['expectOne']>) => void,
  ) {
    const result = gateway.submit(REQUEST).then(
      (value) => ({ value }),
      (error: RecognitionError) => ({ error }),
    );
    respond(backend.expectOne('/api/recognitions'));
    return result;
  }

  it('posts the drawing to the relative /api URL and reads the new job', async () => {
    const result = gateway.submit(REQUEST);
    const call = backend.expectOne('/api/recognitions');
    expect(call.request.method).toBe('POST');
    expect(call.request.body).toEqual(REQUEST);
    call.flush({ job_id: 'abc123', status: 'queued' }, { status: 202, statusText: 'Accepted' });

    await expect(result).resolves.toEqual({ jobId: 'abc123', status: 'queued' });
  });

  it('gets the job state for polling', async () => {
    const result = gateway.get('abc123');
    const call = backend.expectOne('/api/recognitions/abc123');
    expect(call.request.method).toBe('GET');
    call.flush({ job_id: 'abc123', status: 'processing', stroke_order_mode: 'ordered' });

    await expect(result).resolves.toEqual({
      jobId: 'abc123',
      status: 'processing',
      strokeOrderMode: 'ordered',
    });
  });

  it.each([
    [400, 'invalid_drawing', 'invalid_drawing'],
    [413, 'drawing_too_large', 'drawing_too_large'],
    [404, 'job_not_found', 'job_not_found'],
    [400, 'invalid_stroke_order_mode', 'unexpected'],
    [400, 'invalid_request', 'unexpected'],
    [500, 'internal_server_error', 'unexpected'],
  ])('turns a %i with %s into %s', async (status, code, expected) => {
    const result = await submitAnswered((call) =>
      call.flush({ error: code }, { status, statusText: 'Error' }),
    );

    expect((result as { error: RecognitionError }).error.code).toBe(expected);
  });

  it('keeps the Retry-After of a full queue', async () => {
    const result = await submitAnswered((call) =>
      call.flush(
        { error: 'queue_full' },
        { status: 503, statusText: 'Service Unavailable', headers: { 'Retry-After': '7' } },
      ),
    );

    const { error } = result as { error: RecognitionError };
    expect(error.code).toBe('queue_full');
    expect(error.retryAfterSeconds).toBe(7);
  });

  it('waits the API default when a full queue sends no usable Retry-After', async () => {
    const result = await submitAnswered((call) =>
      call.flush({ error: 'queue_full' }, { status: 503, statusText: 'Service Unavailable' }),
    );

    expect((result as { error: RecognitionError }).error.retryAfterSeconds).toBe(
      DEFAULT_RETRY_AFTER_SECONDS,
    );
  });

  it('says there is no connection when nothing answers', async () => {
    const result = await submitAnswered((call) => call.error(new ProgressEvent('error')));

    expect((result as { error: RecognitionError }).error.code).toBe('offline');
  });

  it('says there is no connection when the proxy answers for an API that is down', async () => {
    const result = await submitAnswered((call) =>
      call.flush('connect ECONNREFUSED', { status: 502, statusText: 'Bad Gateway' }),
    );

    expect((result as { error: RecognitionError }).error.code).toBe('offline');
  });

  it('refuses an answer it cannot read as unexpected', async () => {
    const result = await submitAnswered((call) =>
      call.flush({ id: 'abc123' }, { status: 202, statusText: 'Accepted' }),
    );

    expect((result as { error: RecognitionError }).error.code).toBe('unexpected');
  });
});
