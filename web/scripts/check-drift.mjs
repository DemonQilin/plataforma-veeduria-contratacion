// Verifica que nada derive (CLAUDE.md de la raíz, verificaciones 3 a 5):
//  - el contrato regenerado (data/schema y src/types/contract.ts) no cambia;
//  - pipeline/requirements.txt coincide con uv.lock;
//  - la versión de pnpm es la misma en package.json, mise.toml e instrucciones.txt,
//    y la de Node en web/.node-version y mise.toml.
// Compara el contenido antes y después de regenerar, así funciona también con
// cambios sin confirmar en git.
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
import { existsSync, readFileSync, readdirSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const web = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const root = resolve(web, '..');
const pipeline = join(root, 'pipeline');
const errors = [];

const read = (path) => readFileSync(path, 'utf8');

// 1. Versiones
const pnpmVersions = new Map();
const packageManager = JSON.parse(read(join(web, 'package.json'))).packageManager ?? '';
pnpmVersions.set('web/package.json', packageManager.match(/^pnpm@(.+)$/)?.[1]);
pnpmVersions.set('mise.toml', read(join(root, 'mise.toml')).match(/^pnpm\s*=\s*"([^"]+)"/m)?.[1]);
const instructionsPath = join(root, 'instrucciones.txt');
if (existsSync(instructionsPath)) {
  const found = [...read(instructionsPath).matchAll(/pnpm@([0-9][^\s]*)/g)].map((m) => m[1]);
  new Set(found).forEach((version) => pnpmVersions.set(`instrucciones.txt (${version})`, version));
} else {
  errors.push('Falta instrucciones.txt en la raíz.');
}
if (new Set(pnpmVersions.values()).size !== 1) {
  errors.push(`La versión de pnpm no coincide: ${JSON.stringify(Object.fromEntries(pnpmVersions))}`);
}

const nodeFile = read(join(web, '.node-version')).trim();
const nodeMise = read(join(root, 'mise.toml')).match(/^node\s*=\s*"([^"]+)"/m)?.[1];
if (nodeFile !== nodeMise) {
  errors.push(`La versión de Node no coincide: web/.node-version=${nodeFile}, mise.toml=${nodeMise}`);
}

// 2. Contrato y requirements.txt
const generated = () => {
  const files = [
    ...readdirSync(join(root, 'data', 'schema')).map((name) => join(root, 'data', 'schema', name)),
    join(web, 'src', 'types', 'contract.ts'),
    join(pipeline, 'requirements.txt'),
  ].filter(existsSync);
  return new Map(
    files.sort().map((file) => [
      relative(root, file).replaceAll('\\', '/'),
      createHash('sha256').update(readFileSync(file)).digest('hex'),
    ]),
  );
};

const run = (command, args, cwd, stdout = 'inherit') => {
  const result = spawnSync(command, args, { cwd, stdio: ['ignore', stdout, 'inherit'] });
  if (result.status !== 0) {
    console.error(`Falló: ${command} ${args.join(' ')}`);
    process.exit(result.status ?? 1);
  }
};

const before = generated();
run('uv', ['run', '--locked', 'veeduria', 'export-schema'], pipeline);
run(process.execPath, [join(web, 'scripts', 'gen-types.mjs')], web);
// uv escribe el comando en el encabezado del archivo: debe ser el de pipeline/CLAUDE.md.
run('uv', ['lock', '--check'], pipeline);
run('uv', ['export', '--format', 'requirements-txt', '-o', 'requirements.txt'], pipeline, 'ignore');
const after = generated();

for (const path of new Set([...before.keys(), ...after.keys()])) {
  if (before.get(path) !== after.get(path)) {
    errors.push(`${path} cambió al regenerarlo: confírmalo en el mismo commit que su origen.`);
  }
}

if (errors.length > 0) {
  console.error(errors.map((error) => `✗ ${error}`).join('\n'));
  process.exit(1);
}
console.log('✓ Sin deriva: versiones, contrato y requirements.txt coinciden.');