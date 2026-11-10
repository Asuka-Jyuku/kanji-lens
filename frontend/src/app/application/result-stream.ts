import type { RecognitionJob } from '../domain/recognition-job';

export interface ResultStreamHandlers {
  /** Each state the job reaches, complete. After a final one the stream closes by itself. */
  readonly state: (job: RecognitionJob) => void;
  /**
   * The connection broke. `closed` is true when the stream gave up (an answer that is not a
   * stream, such as a 404, or an event it cannot read); otherwise it is trying again.
   */
  readonly error: (closed: boolean) => void;
}

export interface ResultStreamConnection {
  close(): void;
}

/**
 * Port: the job's state changes, pushed by the server (ADR 0020). An abstract class, so it is
 * also the DI token. Whether to fall back to polling is the use case's decision, not the
 * stream's.
 */
export abstract class ResultStream {
  abstract open(jobId: string, handlers: ResultStreamHandlers): ResultStreamConnection;
}
