import type { RecognitionJob, SubmittedJob } from '../domain/recognition-job';
import type { RecognitionRequest } from '../domain/recognition-request';

/**
 * Port: the recognition API (ARCHITECTURE.md, section 5.1). An abstract class, so it is also
 * the DI token; the adapter is wired in app.config.ts (ADR 0004).
 *
 * Both methods reject with a RecognitionError carrying the code the screen translates.
 */
export abstract class RecognitionGateway {
  /** POST /api/recognitions: queues the drawing and answers the new job. */
  abstract submit(request: RecognitionRequest): Promise<SubmittedJob>;

  /** GET /api/recognitions/{id}: the job's current state, the polling fallback (ADR 0020). */
  abstract get(jobId: string): Promise<RecognitionJob>;
}
