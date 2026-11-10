import { Injectable } from '@angular/core';

import {
  ResultStream,
  ResultStreamConnection,
  ResultStreamHandlers,
} from '../application/result-stream';
import { JOB_STATUSES, RecognitionJob, isFinalStatus } from '../domain/recognition-job';
import { readRecognitionJob, recognitionUrl } from './recognition-api';

/**
 * Adapter: the job's state over SSE, with the browser's own EventSource (ADR 0020).
 *
 * The API names each event after the state (`event: completed`) and sends the full state as
 * data, so there is no `message` event to listen to. The stream is closed at the final state,
 * before the server's end of stream would make EventSource reconnect, and whenever the use
 * case closes it (a new recognition, or the screen going away).
 */
@Injectable()
export class SseResultStream extends ResultStream {
  open(jobId: string, handlers: ResultStreamHandlers): ResultStreamConnection {
    const source = new EventSource(`${recognitionUrl(jobId)}/events`);
    let open = true;
    const close = () => {
      open = false;
      source.close();
    };

    const onState = (event: Event) => {
      if (!open) {
        return;
      }
      let job: RecognitionJob;
      try {
        job = readRecognitionJob(JSON.parse((event as MessageEvent<string>).data));
      } catch {
        // An event it cannot read will not get better by waiting: give up on the stream.
        close();
        handlers.error(true);
        return;
      }
      if (isFinalStatus(job.status)) {
        close();
      }
      handlers.state(job);
    };
    for (const status of JOB_STATUSES) {
      source.addEventListener(status, onState);
    }
    source.addEventListener('error', () => {
      if (open) {
        handlers.error(source.readyState === EventSource.CLOSED);
      }
    });

    return { close };
  }
}
