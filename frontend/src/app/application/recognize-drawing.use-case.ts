import { DestroyRef, Injectable, computed, inject, signal } from '@angular/core';

import { RecognitionJob, isFinalStatus } from '../domain/recognition-job';
import { toRecognitionRequest } from '../domain/recognition-request';
import {
  IDLE,
  RecognitionError,
  RecognitionState,
  isInProgress,
  stateOfError,
  stateOfJob,
} from '../domain/recognition-state';
import { DrawingSession } from './drawing-session';
import { RecognitionGateway } from './recognition.gateway';
import { ResultStream, ResultStreamConnection } from './result-stream';

/**
 * When the job is followed by polling instead of SSE, and when it is given up (ADR 0020;
 * the values are the decision of #58, in its PR).
 */
export const FOLLOW_POLICY = {
  /** Stream errors in a row, with no state between them, before switching to polling. */
  streamErrorsBeforePolling: 3,
  /** Between two GET /api/recognitions/{id}. */
  pollIntervalMs: 1_000,
  /** Polls in a row with no connection before telling the user. */
  pollErrorsBeforeGivingUp: 3,
  /** From sending to a final state; past it, the screen says the server took too long. */
  jobTimeoutMs: 60_000,
} as const;

/**
 * Use case: send the drawing and the chosen mode, and follow the job to its end (ADR 0020).
 * The screen reads `state` and `canRecognize`; the result screen (#59) reads `result`.
 *
 * One recognition at a time: "Reconhecer" is off while a job is under way and, after a full
 * queue, for the seconds the API asks (Retry-After).
 */
@Injectable({ providedIn: 'root' })
export class RecognizeDrawing {
  private readonly gateway = inject(RecognitionGateway);
  private readonly stream = inject(ResultStream);
  private readonly drawing = inject(DrawingSession);

  private readonly current = signal<RecognitionState>(IDLE);
  private readonly waitingForQueue = signal(false);
  private watch: JobWatch | null = null;
  private queueTimer: ReturnType<typeof setTimeout> | undefined;

  readonly state = this.current.asReadonly();
  readonly inProgress = computed(() => isInProgress(this.current()));
  readonly canRecognize = computed(
    () => !this.drawing.empty() && !this.inProgress() && !this.waitingForQueue(),
  );
  /** The completed job, for the predictions; null otherwise. */
  readonly result = computed(() => {
    const state = this.current();
    return state.phase === 'completed' ? state.job : null;
  });

  constructor() {
    inject(DestroyRef).onDestroy(() => {
      this.watch?.stop();
      clearTimeout(this.queueTimer);
    });
  }

  async recognize(): Promise<void> {
    if (!this.canRecognize()) {
      return;
    }
    this.watch?.stop();
    this.watch = null;
    const request = toRecognitionRequest(this.drawing.drawing(), this.drawing.mode());
    this.current.set({ phase: 'sending' });
    try {
      const job = await this.gateway.submit(request);
      this.current.set(stateOfJob({ ...job, strokeOrderMode: request.stroke_order_mode }));
      this.watch = new JobWatch(job.jobId, this.gateway, this.stream, {
        job: (update) => this.current.set(stateOfJob(update)),
        error: (error) => this.current.set(stateOfError(error)),
      });
    } catch (error) {
      this.fail(error);
    }
  }

  private fail(error: unknown): void {
    const state = stateOfError(error);
    this.current.set(state);
    if (state.phase === 'failed' && state.retryAfterSeconds !== undefined) {
      this.waitingForQueue.set(true);
      clearTimeout(this.queueTimer);
      this.queueTimer = setTimeout(
        () => this.waitingForQueue.set(false),
        state.retryAfterSeconds * 1_000,
      );
    }
  }
}

interface JobWatchReport {
  readonly job: (job: RecognitionJob) => void;
  readonly error: (error: unknown) => void;
}

/**
 * Follows one job: SSE first, polling when the stream keeps failing, and a time limit. Reports
 * each state until a final one or an error, then stops; nothing is reported after `stop()`.
 */
class JobWatch {
  private connection: ResultStreamConnection | null;
  private readonly timers = new Set<ReturnType<typeof setTimeout>>();
  private streamErrors = 0;
  private pollErrors = 0;
  private stopped = false;

  constructor(
    private readonly jobId: string,
    private readonly gateway: RecognitionGateway,
    stream: ResultStream,
    private readonly report: JobWatchReport,
  ) {
    this.later(FOLLOW_POLICY.jobTimeoutMs, () => this.fail(new RecognitionError('timeout')));
    this.connection = stream.open(jobId, {
      state: (job) => this.onStreamState(job),
      error: (closed) => this.onStreamError(closed),
    });
  }

  stop(): void {
    this.stopped = true;
    this.connection?.close();
    this.connection = null;
    this.timers.forEach(clearTimeout);
    this.timers.clear();
  }

  private onStreamState(job: RecognitionJob): void {
    if (this.stopped) {
      return;
    }
    this.streamErrors = 0;
    this.publish(job);
  }

  private onStreamError(closed: boolean): void {
    if (this.stopped || this.connection === null) {
      return;
    }
    this.streamErrors += 1;
    if (closed || this.streamErrors >= FOLLOW_POLICY.streamErrorsBeforePolling) {
      this.connection.close();
      this.connection = null;
      void this.poll();
    }
  }

  private async poll(): Promise<void> {
    try {
      const job = await this.gateway.get(this.jobId);
      if (this.stopped) {
        return;
      }
      this.pollErrors = 0;
      this.publish(job);
    } catch (error) {
      if (this.stopped) {
        return;
      }
      // Only a lost connection is worth another try; any other answer is the job's end.
      const offline = error instanceof RecognitionError && error.code === 'offline';
      this.pollErrors += 1;
      if (!offline || this.pollErrors >= FOLLOW_POLICY.pollErrorsBeforeGivingUp) {
        this.fail(error);
        return;
      }
    }
    if (!this.stopped) {
      this.later(FOLLOW_POLICY.pollIntervalMs, () => void this.poll());
    }
  }

  private publish(job: RecognitionJob): void {
    this.report.job(job);
    if (isFinalStatus(job.status)) {
      this.stop();
    }
  }

  private fail(error: unknown): void {
    if (this.stopped) {
      return;
    }
    this.stop();
    this.report.error(error);
  }

  private later(ms: number, action: () => void): void {
    const timer = setTimeout(() => {
      this.timers.delete(timer);
      action();
    }, ms);
    this.timers.add(timer);
  }
}
