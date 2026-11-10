// Fails when a development-only tool reached the production build in dist/ (#66): the drawing
// export saves drawings, and in production no drawing leaves the device (CLAUDE.md,
// "Segurança"). Run after `npm run build`; app.dev-tools.ts says how the tools are left out.
import { readFileSync, readdirSync } from 'node:fs';
import { join } from 'node:path';

const DIST = 'dist';
// The component selector, the file format and the panel title: any of them means it is there.
const MARKERS = ['app-drawing-export', 'kanjilens-drawing', 'Exportar desenho'];

function scripts(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const path = join(dir, entry.name);
    if (entry.isDirectory()) {
      return scripts(path);
    }
    return entry.name.endsWith('.js') ? [path] : [];
  });
}

let files;
try {
  files = scripts(DIST);
} catch {
  files = [];
}
if (files.length === 0) {
  console.error(`No JavaScript in ${DIST}/: run "npm run build" first.`);
  process.exit(1);
}

const found = files.flatMap((file) => {
  const code = readFileSync(file, 'utf8');
  return MARKERS.filter((marker) => code.includes(marker)).map((marker) => `${file}: ${marker}`);
});
if (found.length > 0) {
  console.error('Development-only code in the production build:');
  for (const line of found) {
    console.error(`  ${line}`);
  }
  process.exit(1);
}
console.log(`No development-only tool in the ${files.length} production scripts.`);
