import type { Type } from '@angular/core';

import { DrawingExport } from './presentation/drawing-export/drawing-export';

/**
 * The development-only tool, in the development build (`ng serve`, tests), which puts this
 * file in place of app.dev-tools.ts: the drawing export for the test sets (#66).
 */
export const DEV_TOOL: Type<unknown> | null = DrawingExport;
