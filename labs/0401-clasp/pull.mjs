import { spawnSync } from 'node:child_process';
import { existsSync, mkdirSync, mkdtempSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const [scriptId, ...extra] = process.argv.slice(2);
if (extra.length || !/^[A-Za-z0-9_-]{35,200}$/.test(scriptId ?? '')) {
  console.error('Indica únicamente el ID de secuencia de comandos del laboratorio 04.01.');
  process.exit(2);
}

// Una descarga nueva nunca sobreescribe fuentes del repositorio ni una descarga anterior.
const local = fileURLToPath(new URL('../../.local/0401-clasp/', import.meta.url));
mkdirSync(local, { recursive: true, mode: 0o700 });
const directory = mkdtempSync(join(local, 'pull-'));
const config = join(directory, '.clasp.json');
const source = join(directory, 'src');
writeFileSync(config, JSON.stringify({
  scriptId,
  rootDir: 'src',
}, null, 2), { mode: 0o600 });
mkdirSync(source, { mode: 0o700 });

const result = spawnSync('npm', [
  'exec', '--yes', '--package=@google/clasp@3.4.1', '--', 'clasp', '--project', config, 'pull',
], { cwd: directory, stdio: 'inherit' });
if (result.error || result.status !== 0) {
  console.error('Falló la descarga del código. Revisa la sesión de clasp y el acceso al proyecto.');
  process.exit(result.status || 1);
}
if (!existsSync(join(source, 'appsscript.json'))) {
  console.error('La descarga no contiene el manifiesto appsscript.json.');
  process.exit(1);
}
console.log('Código descargado en ' + source);
