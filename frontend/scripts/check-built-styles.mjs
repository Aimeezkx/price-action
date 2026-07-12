import { readdir, readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const assetsDirectory = new URL('../dist/assets/', import.meta.url);
const cssFiles = (await readdir(assetsDirectory)).filter((name) => name.endsWith('.css'));

if (cssFiles.length === 0) {
  throw new Error('No compiled CSS asset was produced.');
}

const css = (await Promise.all(
  cssFiles.map((name) => readFile(join(fileURLToPath(assetsDirectory), name), 'utf8')),
)).join('\n');

const requiredUtilities = ['.min-h-screen', '.bg-white', '.rounded-lg', '.text-gray-900'];
const missingUtilities = requiredUtilities.filter((utility) => !css.includes(utility));

if (css.length < 10_000 || missingUtilities.length > 0) {
  throw new Error(
    `Compiled UI styles are incomplete (${css.length} bytes). Missing: ${missingUtilities.join(', ') || 'none'}`,
  );
}

console.log(`Compiled UI styles verified: ${css.length} bytes across ${cssFiles.length} asset(s).`);
