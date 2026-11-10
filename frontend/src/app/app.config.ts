import { provideHttpClient, withFetch } from '@angular/common/http';
import { ApplicationConfig, provideBrowserGlobalErrorListeners } from '@angular/core';
import { provideRouter } from '@angular/router';

import { DEV_PROVIDERS } from './app.dev-tools';
import { routes } from './app.routes';
import { RecognitionGateway } from './application/recognition.gateway';
import { ResultStream } from './application/result-stream';
import { HttpRecognitionGateway } from './infrastructure/http-recognition.gateway';
import { SseResultStream } from './infrastructure/sse-result-stream';

export const appConfig: ApplicationConfig = {
  providers: [
    provideBrowserGlobalErrorListeners(),
    provideRouter(routes),
    provideHttpClient(withFetch()),
    // The ports and their adapters meet only here (ADR 0004).
    { provide: RecognitionGateway, useClass: HttpRecognitionGateway },
    { provide: ResultStream, useClass: SseResultStream },
    ...DEV_PROVIDERS,
  ],
};
