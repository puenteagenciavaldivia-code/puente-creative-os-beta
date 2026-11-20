import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { cpSync, mkdirSync, mkdtempSync, readdirSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

test('clasp solo sube los tres archivos tras crear un proyecto independiente nuevo', () => {
  const root = mkdtempSync(join(tmpdir(), 'puente-clasp-create-'));
  try {
    const lab = join(root, 'labs', '0401-clasp');
    const bin = join(root, 'bin');
    mkdirSync(bin);
    cpSync(new URL('.', import.meta.url), lab, { recursive: true });
    writeFileSync(join(bin, 'npm'), [
      '#!/bin/sh',
      'set -eu',
      'test "$6" = --project && test "$7" = "$PWD"',
      'case "$8" in',
      '  create-script)',
      '    test ! -f .clasp.json && test "${10}" = standalone || exit 8',
      '    test "$TEST_CREATE" = fail && exit 6',
      `    printf '%s' '{"scriptId":"synthetic_synthetic_synthetic_synthetic_synthetic","rootDir":"src"}' > .clasp.json`,
      '    : > src/Code.js ;;',
      '  push)',
      '    test "$9" = --force && test -f .clasp.json',
      '    test -f src/Receiver.js && test -f src/LabChecks.js && test -f src/appsscript.json',
      '    test ! -e src/Code.js',
      '    : > pushed ;;',
      '  *) exit 9 ;;',
      'esac',
    ].join('\n'), { mode: 0o700 });

    const run = (outcome, ...args) => spawnSync(process.execPath, [join(lab, 'create-lab.mjs'), ...args], {
      env: { ...process.env, PATH: bin, TEST_CREATE: outcome }, encoding: 'utf8',
    });
    assert.equal(run('ok', 'existing-project').status, 2);
    assert.equal(run('fail').status, 1);
    const result = run('ok');
    assert.equal(result.status, 0, result.stderr);
    const region = join(root, '.local', '0401-clasp');
    const downloads = readdirSync(region);
    assert.equal(downloads.length, 2);
    assert.equal(downloads.filter(path => readdirSync(join(region, path)).includes('pushed')).length, 1);
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
