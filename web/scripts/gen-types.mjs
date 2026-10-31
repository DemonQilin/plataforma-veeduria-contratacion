// Genera src/types/contract.ts desde data/schema/*.json (docs/adr/0004).
// Nunca se edita a mano el archivo generado: el cambio va en los modelos de Pydantic.
import { readdir, writeFile, mkdir } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { compileFromFile } from 'json-schema-to-typescript';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const schemaDir = resolve(root, '..', 'data', 'schema');
const target = resolve(root, 'src', 'types', 'contract.ts');

const banner =
  '// Archivo generado por `pnpm gen:types` desde data/schema/. No lo edites a mano.\n\n';

const names = (await readdir(schemaDir)).filter((name) => name.endsWith('.json')).sort();
const parts = [];
for (const name of names) {
  parts.push(await compileFromFile(join(schemaDir, name), { bannerComment: '' }));
}

await mkdir(dirname(target), { recursive: true });
await writeFile(target, (banner + parts.join('\n')).replace(/\r\n/g, '\n'), 'utf8');
console.log(`Escrito ${target} (${names.length} esquemas)`);