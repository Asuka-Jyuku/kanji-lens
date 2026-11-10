import type { Type } from '@angular/core';

/**
 * The development-only tool, as the production build sees it: none. The development build
 * swaps this file for app.dev-tools.development.ts (angular.json, `fileReplacements`), so the
 * drawing export (#66) never reaches production, where no drawing leaves the device
 * (CLAUDE.md, "Segurança"). `npm run check:production-bundle` checks it after the build.
 */
export const DEV_TOOL: Type<unknown> | null = null;
