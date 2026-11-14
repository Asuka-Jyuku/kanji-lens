import type { Type } from '@angular/core';

import { CollectionSession } from './presentation/collection-session/collection-session';
import { DrawingExport } from './presentation/drawing-export/drawing-export';

/**
 * The development-only tools, in the development build (`ng serve`, tests), which puts this
 * file in place of app.dev-tools.ts: the drawing export for the test sets (#66) and the
 * collection session for the real recognition set (#100).
 */
export const DEV_TOOLS: readonly Type<unknown>[] = [DrawingExport, CollectionSession];
