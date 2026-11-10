import type { Provider, Type } from '@angular/core';

/**
 * Development-only tools, as the production build sees them: none. The development build
 * swaps this file for app.dev-tools.development.ts (angular.json, `fileReplacements`), so the
 * drawing export (#66) never reaches production, where no drawing leaves the device
 * (CLAUDE.md, "Segurança"). `npm run check:production-bundle` checks it after the build.
 */
export const DEV_TOOLS: readonly Type<unknown>[] = [];

export const DEV_PROVIDERS: Provider[] = [];
