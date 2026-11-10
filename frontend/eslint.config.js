// @ts-check
const eslint = require('@eslint/js');
const { defineConfig } = require('eslint/config');
const tseslint = require('typescript-eslint');
const angular = require('angular-eslint');
const boundaries = require('eslint-plugin-boundaries');

// Architecture test (CLAUDE.md, "Testes"; ADR 0004 and 0017): which layer may import which,
// and which packages each layer may use. A broken rule is an ESLint error, so `npm run lint` fails.
const layers = {
  'boundaries/elements': [
    { type: 'domain', pattern: 'src/app/domain' },
    { type: 'application', pattern: 'src/app/application' },
    { type: 'infrastructure', pattern: 'src/app/infrastructure' },
    { type: 'presentation', pattern: 'src/app/presentation' },
  ],
  // Shell files (main.ts, app.ts, app.config.ts, app.routes.ts) are the composition root.
  'boundaries/files': [{ pattern: ['src/app/app*.ts', 'src/main.ts'], category: 'shell' }],
  'import/resolver': { typescript: { alwaysTryTypes: true } },
};

const layerPolicies = [
  'error',
  {
    default: 'disallow',
    // Also check imports of packages (external and Node core), not only local files.
    checkAllOrigins: true,
    policies: [
      // Domain: pure TypeScript, nothing from Angular or any other package.
      { from: { element: { type: 'domain' } }, allow: { to: { element: { type: 'domain' } } } },
      // Application: use cases and ports; may use signals and DI from @angular/core only.
      {
        from: { element: { type: 'application' } },
        allow: [
          { to: { element: { types: ['domain', 'application'] } } },
          { to: { module: { source: '@angular/core' } } },
        ],
      },
      // Infrastructure: adapters; may use any package (HttpClient, EventSource helpers, rxjs).
      {
        from: { element: { type: 'infrastructure' } },
        allow: [
          { to: { element: { types: ['domain', 'application', 'infrastructure'] } } },
          { to: { module: { origin: ['external', 'core'] } } },
        ],
      },
      // Presentation: components only talk to the application layer; never HttpClient.
      {
        from: { element: { type: 'presentation' } },
        allow: [
          { to: { element: { types: ['domain', 'application', 'presentation'] } } },
          { to: { module: { source: '@angular/*' } } },
        ],
      },
      {
        from: { element: { type: 'presentation' } },
        disallow: { to: { module: { source: '@angular/common', internalPath: 'http{,/**}' } } },
        message: 'Components never use HttpClient: they talk to the application layer (ADR 0004)',
      },
      // Shell (main.ts, app.ts, app.config.ts, app.routes.ts): composition root, wires everything.
      {
        from: { file: { categories: 'shell' } },
        allow: [
          {
            to: {
              element: {
                types: ['domain', 'application', 'infrastructure', 'presentation'],
              },
            },
          },
          { to: { module: { origin: ['external', 'core'] } } },
          { to: { file: { categories: 'shell' } } },
        ],
      },
    ],
  },
];

module.exports = defineConfig([
  {
    files: ['**/*.ts'],
    extends: [
      eslint.configs.recommended,
      tseslint.configs.recommended,
      tseslint.configs.stylistic,
      angular.configs.tsRecommended,
    ],
    processor: angular.processInlineTemplates,
    rules: {
      '@angular-eslint/directive-selector': [
        'error',
        { type: 'attribute', prefix: 'app', style: 'camelCase' },
      ],
      '@angular-eslint/component-selector': [
        'error',
        { type: 'element', prefix: 'app', style: 'kebab-case' },
      ],
    },
  },
  {
    files: ['src/**/*.ts'],
    ignores: ['src/**/*.spec.ts'],
    plugins: { boundaries },
    settings: layers,
    rules: { 'boundaries/dependencies': layerPolicies },
  },
  {
    files: ['**/*.html'],
    extends: [angular.configs.templateRecommended, angular.configs.templateAccessibility],
  },
  {
    files: ['src/app/**/*.html'],
    rules: {
      // Every visible text in a component template goes through i18n (ADR 0009 and 0017).
      '@angular-eslint/template/i18n': [
        'error',
        {
          checkId: true,
          checkText: true,
          checkAttributes: true,
          requireDescription: false,
          // These hold element ids (the ARIA ones) or a keyboard type (inputmode), not text:
          // nothing to translate.
          ignoreAttributes: [
            'aria-describedby',
            'aria-labelledby',
            'aria-controls',
            'aria-owns',
            'inputmode',
          ],
        },
      ],
    },
  },
]);
