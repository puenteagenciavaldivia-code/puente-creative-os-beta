import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const source = readFileSync(new URL('../../apps_script.gs', import.meta.url), 'utf8');
const id = 'f0000000-0000-4000-8000-000000000001';
const syntheticToken = 'fixture-only';

function harness({ failLinkOnce = false } = {}) {
  const files = new Map();
  let link = '';
  let acquired = false;
  let opened = 0;
  const iterable = value => ({ hasNext: () => value !== undefined, next: () => value });
  const folder = {
    getFilesByName: name => iterable(files.get(name)),
    createFile(blob) {
      assert.ok(acquired);
      const fileNumber = files.size + 1;
      const saved = { blob, getUrl: () => 'synthetic-file-' + fileNumber };
      files.set(blob.name, saved);
      return saved;
    },
  };
  const sheet = {
    getLastRow: () => 2,
    getRange(row, column) {
      if (row === 2 && column === 2) return { getDisplayValues: () => [[id]] };
      if (row === 1 && column === 11) return { getValue: () => 'adjuntos_drive' };
      assert.deepEqual([row, column], [2, 11]);
      return {
        getValue: () => link,
        setValue(value) {
          if (failLinkOnce) {
            failLinkOnce = false;
            throw new Error('Interrupción sintética después de crear el archivo');
          }
          link = value;
        },
      };
    },
  };
  const context = {
    ContentService: { createTextOutput: value => value },
    PropertiesService: { getScriptProperties: () => ({ getProperty: () => syntheticToken }) },
    LockService: { getScriptLock: () => ({
      waitLock: () => { acquired = true; },
      hasLock: () => acquired,
      releaseLock: () => { acquired = false; },
    }) },
    SpreadsheetApp: { openById: () => {
      opened++;
      return { getSheetByName: () => sheet };
    } },
    DriveApp: { getFoldersByName: () => iterable({
      getFoldersByName: () => iterable(folder),
    }) },
    Utilities: {
      base64Decode: data => Buffer.from(data, 'base64'),
      newBlob: (bytes, mime, name) => ({ bytes, mime, name }),
    },
    console: { error: () => {} },
  };
  runInNewContext(source, context);
  function send(overrides = {}, content = '%PDF-1.4\nfixture') {
    return context.doPost({ postData: { contents: JSON.stringify({
      action: 'attachments',
      token: syntheticToken,
      submission_id: id,
      attachment_key: 'a'.repeat(64),
      files_consent: false,
      files: [{ name: 'sintetico.pdf', mime: 'application/pdf', data: Buffer.from(content).toString('base64') }],
      ...overrides,
    }) } });
  }
  return { send, files, link: () => link, opened: () => opened };
}

test('Beta rechaza token inválido antes de abrir la hoja', () => {
  const lab = harness();
  assert.equal(lab.send({ token: 'otro-valor' }), 'DENIED');
  assert.equal(lab.opened(), 0);
  assert.equal(lab.files.size, 0);
});

test('Beta rechaza un submission desconocido y no crea archivos', () => {
  const lab = harness();
  assert.equal(lab.send({ submission_id: 'f0000000-0000-4000-8000-000000000002' }), 'INVALID');
  assert.equal(lab.files.size, 0);
});

test('Beta acepta sin consentimiento y reutiliza un archivo del mismo nombre con bytes distintos', () => {
  const lab = harness();
  assert.equal(lab.send(), 'OK');
  assert.equal(lab.send({}, '%PDF-1.4\nother'), 'OK');
  assert.equal(lab.files.size, 1);
  assert.equal(lab.files.get('sintetico.pdf').blob.bytes.toString(), '%PDF-1.4\nfixture');
  assert.equal(lab.link(), 'synthetic-file-1');
});

test('Beta recupera una interrupción simulada por nombre y agrega el enlace al reintentar', () => {
  const lab = harness({ failLinkOnce: true });
  assert.equal(lab.send(), 'ERROR');
  assert.equal(lab.link(), '');
  assert.equal(lab.files.size, 1);
  assert.equal(lab.send(), 'OK');
  assert.equal(lab.link(), 'synthetic-file-1');
  assert.equal(lab.files.size, 1);
});

test('Beta admite contenido sin firma PDF cuando se declara como PDF', () => {
  const lab = harness();
  assert.equal(lab.send({}, 'solo texto'), 'OK');
  assert.equal(lab.files.size, 1);
});
