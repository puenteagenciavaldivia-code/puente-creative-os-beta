import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readFileSync, readdirSync, rmSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

if (process.argv.length !== 2) {
  console.error('Este comando crea un proyecto nuevo y no acepta un ID existente.');
  process.exit(2);
}

const local = fileURLToPath(new URL('../../.local/0401-clasp/', import.meta.url));
mkdirSync(local, { recursive: true, mode: 0o700 });
const directory = mkdtempSync(join(local, 'receiver-'));
const src = join(directory, 'src');
mkdirSync(src, { mode: 0o700 });

function clasp(...args) {
  const result = spawnSync('npm', [
    'exec', '--yes', '--package=@google/clasp@3.4.1', '--',
    'clasp', '--project', directory, ...args,
  ], { cwd: directory, stdio: 'inherit' });
  if (result.error || result.status !== 0) {
    throw new Error('Falló clasp ' + args[0]);
  }
}

try {
  clasp('create-script', '--type', 'standalone', '--title',
    'PUENTE 04.01 — receptor sintético aislado', '--rootDir', 'src');
  const config = JSON.parse(readFileSync(join(directory, '.clasp.json'), 'utf8'));
  if (!/^[A-Za-z0-9_-]{35,200}$/.test(config.scriptId ?? '') ||
      config.rootDir !== 'src' || config.parentId) {
    throw new Error('Configuración inesperada del proyecto nuevo');
  }
  // The standalone project directory was created by this invocation.
  for (const name of readdirSync(src)) rmSync(join(src, name), { recursive: true });
  for (const name of ['Receiver.js', 'LabChecks.js', 'appsscript.json']) {
    copyFileSync(new URL('./receiver/' + name, import.meta.url), join(src, name));
  }
  clasp('push', '--force');
  console.log('Proyecto aislado preparado: ' + directory);
} catch (error) {
  console.error(error.message);
  process.exitCode = 1;
}
