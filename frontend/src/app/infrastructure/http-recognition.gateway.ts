import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, firstValueFrom } from 'rxjs';

import { RecognitionGateway } from '../application/recognition.gateway';
import { RecognitionJob, SubmittedJob } from '../domain/recognition-job';
import { RecognitionRequest } from '../domain/recognition-request';
import { RecognitionError, RecognitionErrorCode } from '../domain/recognition-state';
import {
  RECOGNITIONS_URL,
  readRecognitionJob,
  readSubmittedJob,
  recognitionUrl,
} from './recognition-api';

/** The API's error codes the screen has a message for; the others are `unexpected`. */
const API_ERRORS: ReadonlySet<string> = new Set<RecognitionErrorCode>([
  'queue_full',
  'invalid_drawing',
  'drawing_too_large',
  'job_not_found',
]);

/** What the gateway answers when the server sends no usable Retry-After (the API's own value). */
export const DEFAULT_RETRY_AFTER_SECONDS = 5;

/**
 * Adapter: the recognition API over HttpClient (ARCHITECTURE.md, sections 5.1 and 5.3).
 * Every failure becomes a RecognitionError with a code; the server's text never reaches the
 * screen (ADR 0009).
 */
@Injectable()
export class HttpRecognitionGateway extends RecognitionGateway {
  private readonly http = inject(HttpClient);

  submit(request: RecognitionRequest): Promise<SubmittedJob> {
    return this.read(this.http.post<unknown>(RECOGNITIONS_URL, request), readSubmittedJob);
  }

  get(jobId: string): Promise<RecognitionJob> {
    return this.read(this.http.get<unknown>(recognitionUrl(jobId)), readRecognitionJob);
  }

  private async read<T>(answer: Observable<unknown>, parse: (body: unknown) => T): Promise<T> {
    let body: unknown;
    try {
      body = await firstValueFrom(answer);
    } catch (error) {
      throw toRecognitionError(error);
    }
    return parse(body);
  }
}

export function toRecognitionError(error: unknown): RecognitionError {
  if (!(error instanceof HttpErrorResponse)) {
    return new RecognitionError('unexpected');
  }
  const code = apiErrorCode(error.error);
  if (code === 'queue_full') {
    return new RecognitionError(code, retryAfterSeconds(error.headers.get('Retry-After')));
  }
  if (code !== null && API_ERRORS.has(code)) {
    return new RecognitionError(code as RecognitionErrorCode);
  }
  // No answer at all (0), or a server error without one of our codes: the dev proxy (or
  // whatever stands in front of the API) answering for an API that is down.
  if (error.status === 0 || (code === null && error.status >= 500)) {
    return new RecognitionError('offline');
  }
  return new RecognitionError('unexpected');
}

function apiErrorCode(body: unknown): string | null {
  if (typeof body === 'object' && body !== null && 'error' in body) {
    const { error } = body as { error: unknown };
    return typeof error === 'string' ? error : null;
  }
  return null;
}

/** Retry-After in seconds (the API sends a number; an HTTP date is not expected). */
function retryAfterSeconds(header: string | null): number {
  const seconds = Number(header);
  return header !== null && header.trim() !== '' && Number.isInteger(seconds) && seconds >= 0
    ? seconds
    : DEFAULT_RETRY_AFTER_SECONDS;
}
