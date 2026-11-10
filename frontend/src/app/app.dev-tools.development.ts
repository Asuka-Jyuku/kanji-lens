import type { Provider, Type } from '@angular/core';

import { FileDownload } from './application/file-download';
import { BrowserFileDownload } from './infrastructure/browser-file-download';
import { DrawingExport } from './presentation/drawing-export/drawing-export';

/**
 * Development-only tools, in the development build (`ng serve`, tests), which puts this file
 * in place of app.dev-tools.ts: the drawing export for the test sets (#66).
 */
export const DEV_TOOLS: readonly Type<unknown>[] = [DrawingExport];

export const DEV_PROVIDERS: Provider[] = [{ provide: FileDownload, useClass: BrowserFileDownload }];
