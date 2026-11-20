import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { copyFileSync, mkdirSync, mkdtempSync, readdirSync, readFileSync, rmSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';

test('pull valida el ID, aísla las descargas y propaga errores', () => {
  const root = mkdtempSync(join(tmpdir(), 'puente-clasp-test-'));
  try {
    const lab = join(root, 'labs', '0401-clasp');
    const bin = join(root, 'bin');
    mkdirSync(lab, { recursive: true });
    mkdirSync(bin);
    const script = join(lab, 'pull.mjs');
    copyFileSync(new URL('./pull.mjs', import.meta.url), script);
    writeFileSync(join(bin, 'npm'), [
      '#!/bin/sh',
      'test "$*" = "exec --yes --package=@google/clasp@3.4.1 -- clasp --project $PWD/.clasp.json pull" || exit 8',
      'test -f .clasp.json && test -d src || exit 9',
      'if test "$TEST_PULL_STATUS" = 0; then echo "{}" > src/appsscript.json; fi',
      'if test "$TEST_PULL_STATUS" = missing; then exit 0; fi',
      'exit "${TEST_PULL_STATUS:-0}"',
    ].join('\n'), { mode: 0o700 });
    const run = (id, status) => spawnSync(process.execPath, [script, id], {
      env: { ...process.env, PATH: bin, TEST_PULL_STATUS: status },
      encoding: 'utf8',
    });
    const local = join(root, '.local', '0401-clasp');
    assert.equal(run('../invalid', '0').status, 2);
    assert.ok(!readdirSync(root).includes('.local'));

    const scriptId = 'synthetic_'.repeat(5);
    assert.equal(run(scriptId, '0').status, 0);
    assert.equal(run(scriptId, '7').status, 7);
    assert.equal(run(scriptId, 'missing').status, 1);
    const downloads = readdirSync(local);
    assert.equal(downloads.length, 3);
    for (const download of downloads) {
      assert.deepEqual(JSON.parse(readFileSync(join(local, download, '.clasp.json'), 'utf8')), {
        scriptId, rootDir: 'src',
      });
    }
  } finally {
    rmSync(root, { recursive: true, force: true });
  }
});
