import assert from 'node:assert/strict';
import { createHash, randomUUID } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';
import { runInNewContext } from 'node:vm';

const sources = ['Receiver.js', 'LabChecks.js'].map(name =>
  readFileSync(new URL('./receiver/' + name, import.meta.url), 'utf8'));
const digest = bytes => createHash('sha256').update(bytes).digest('hex');
const fixtureToken = 'synthetic-test-value'.repeat(3);
const first = 'f0000000-0000-4000-8000-000000000001';
const second = 'f0000000-0000-4000-8000-000000000002';
const folderType = 'application/vnd.google-apps.folder';

function payload({ id = first, name = 'Diseño.pdf', token = fixtureToken, content = '%PDF-1.4\nfixture' } = {}) {
  const mime = 'application/pdf';
  return {
    action: 'attachments', token, submission_id: id,
    attachment_key: digest(JSON.stringify([name, mime, digest(content)])),
    files: [{ name, mime, data: Buffer.from(content).toString('base64') }],
  };
}

function harness({ fresh = false } = {}) {
  const props = new Map();
  const files = new Map();
  const logs = [];
  const switches = { locked: false, public: false, uncertain: false, failedBeforeWrite: false };
  let nextId = 0;
  let allocated = 0;
  let locked = false;
  if (!fresh) {
    props.set('0401:tokenHash', digest(fixtureToken));
    props.set('0401:root', 'root');
    props.set('0401:submission:' + first, 'granted');
    props.set('0401:submission:' + second, 'granted');
    files.set('root', { id: 'root', mimeType: folderType });
  }
  const properties = {
    getProperty: key => props.get(key) ?? null,
    getKeys: () => [...props.keys()],
    setProperty: (key, value) => props.set(key, value),
    setProperties: values => Object.entries(values).forEach(([key, value]) => props.set(key, value)),
    deleteProperty: key => props.delete(key),
  };
  const context = {
    PropertiesService: { getScriptProperties: () => properties },
    LockService: { getScriptLock: () => ({
      tryLock: () => {
        if (locked || switches.locked) return false;
        locked = true;
        return true;
      },
      waitLock() { assert.ok(this.tryLock()); },
      releaseLock: () => { assert.ok(locked); locked = false; },
    }) },
    Drive: {
      Permissions: { list: () => ({
        permissions: [{ type: 'user', role: switches.public ? 'reader' : 'owner' }],
      }) },
      Files: {
        generateIds: () => {
          assert.ok(locked);
          allocated++;
          return { ids: ['id-' + ++nextId] };
        },
        create: (metadata, blob) => {
          assert.ok(locked);
          const id = metadata.id || 'folder-' + ++nextId;
          if (files.has(id) || switches.failedBeforeWrite) throw new Error('Create failed');
          if (blob) assert.ok([...props.values()].some(value =>
            value.includes('"state":"PENDING"') && value.includes('"fileId":"' + id + '"')));
          const file = { ...metadata, id, ...(blob ? { sha256Checksum: digest(blob) } : {}) };
          files.set(id, file);
          if (switches.uncertain) throw new Error('Response lost after commit');
          return file;
        },
        get: id => {
          if (!files.has(id)) throw new Error('Not found');
          return files.get(id);
        },
        list: () => ({ files: [...files.values()].filter(file => file.mimeType !== folderType) }),
      },
    },
    Utilities: {
      DigestAlgorithm: { SHA_256: 'sha256' },
      Charset: { UTF_8: 'UTF-8' },
      computeDigest: (_, bytes) => Buffer.from(digest(bytes), 'hex'),
      base64Decode: data => Buffer.from(data, 'base64'),
      base64Encode: data => Buffer.from(data).toString('base64'),
      newBlob: bytes => bytes,
      getUuid: randomUUID,
    },
    ContentService: { createTextOutput: value => ({ getContent: () => value }) },
    console: { info: event => logs.push(event) },
  };

  const load = () => {
    const sandbox = { ...context };
    runInNewContext(sources.join('\n'), sandbox);
    return {
      run: value => sandbox.doPost({ postData: { contents: JSON.stringify(value) } }).getContent(),
      receive: sandbox.receiveAttachment_,
      realChecks: sandbox.runSyntheticLab0401,
    };
  };
  return { load, props, files, logs, switches, allocated: () => allocated };
}

test('persiste y reutiliza el mismo ID tras una interrupción en otra ejecución', () => {
  const env = harness();
  assert.equal(env.load().receive(payload(), () => { throw Error('interrupted'); }), 'RETRY');
  assert.equal(env.files.size, 2);
  assert.ok([...env.props.values()].some(value => value.includes('"state":"PENDING"')));
  assert.equal(env.load().run(payload()), 'OK');
  assert.equal(env.load().run(payload()), 'OK');
  assert.equal(env.files.size, 2);
  assert.equal(env.allocated(), 1);
  assert.deepEqual(env.logs.filter(log => log.operation).map(log => log.event),
    ['pending', 'retry', 'reconciled', 'replayed']);
  assert.equal(new Set(env.logs.map(log => log.operation)).size, 1);
  assert.doesNotMatch(JSON.stringify(env.logs), /synthetic-test-value|Diseño\.pdf|id-1|f0000000/);
});

test('recupera respuesta Drive perdida después de guardar y timeout del cliente', () => {
  const env = harness();
  env.switches.uncertain = true;
  assert.equal(env.load().run(payload()), 'OK');
  assert.equal(env.load().run(payload()), 'OK');
  assert.equal(env.files.size, 2);
});

test('si Drive falla antes de escribir, reserva el mismo ID y reintenta', () => {
  const env = harness();
  env.switches.failedBeforeWrite = true;
  assert.equal(env.load().run(payload()), 'RETRY');
  assert.equal(env.files.size, 1);
  env.switches.failedBeforeWrite = false;
  assert.equal(env.load().run(payload()), 'OK');
  assert.equal(env.allocated(), 1);
});

test('la contención devuelve RETRY sin reservar ni escribir', () => {
  const env = harness();
  env.switches.locked = true;
  assert.equal(env.load().run(payload()), 'RETRY');
  assert.equal(env.allocated(), 0);
  env.switches.locked = false;
  assert.equal(env.load().run(payload()), 'OK');
});

test('deniega credenciales, consentimiento y permisos inapropiados sin escribir', () => {
  const env = harness();
  assert.equal(env.load().run(payload({ token: 'incorrecto' })), 'DENIED');
  assert.equal(env.load().run({ ...payload({ id: randomUUID() }), files_consent: true }), 'DENIED');
  env.props.set('0401:submission:' + first, 'revoked');
  assert.equal(env.load().run(payload()), 'DENIED');
  env.switches.public = true;
  assert.equal(env.load().run(payload({ id: second })), 'DENIED');
  assert.equal(env.allocated(), 0);
  assert.equal(env.files.size, 1);
});

test('un PENDING revocado no puede completar el registro', () => {
  const env = harness();
  assert.equal(env.load().receive(payload(), () => { throw Error('interrupted'); }), 'RETRY');
  env.props.set('0401:submission:' + first, 'revoked');
  assert.equal(env.load().run(payload()), 'DENIED');
  assert.ok([...env.props.values()].some(value => value.includes('"state":"PENDING"')));
});

test('rechaza clave alterada, MIME incompatible, base64 irregular y tamaño excesivo', () => {
  const env = harness();
  const original = payload();
  for (const data of ['JVBERi0xLjQ=====', 'JVBE!!', Buffer.alloc(3 * 1024 * 1024 + 1).toString('base64')]) {
    assert.equal(env.load().run({ ...original, files: [{ ...original.files[0], data }] }), 'INVALID');
  }
  assert.equal(env.load().run({ ...payload({ content: '%PDF-1.4\nchanged' }),
    attachment_key: original.attachment_key }), 'INVALID');
  assert.equal(env.load().run(payload({ content: 'texto' })), 'INVALID');
  assert.equal(env.load().run(payload({ name: '../archivo.pdf' })), 'INVALID');
  assert.equal(env.files.size, 1);
});

test('misma clave entre envíos separados y máximo cinco archivos por envío', () => {
  const env = harness();
  for (let n = 0; n < 5; n++) assert.equal(env.load().run(payload({ name: `fixture-${n}.pdf` })), 'OK');
  assert.equal(env.load().run(payload({ name: 'fixture-5.pdf' })), 'INVALID');
  assert.equal(env.load().run(payload({ id: second, name: 'fixture-0.pdf' })), 'OK');
  assert.equal(env.files.size, 7);
});

test('no confirma un archivo alterado ni lo reemplaza automáticamente', () => {
  const env = harness();
  assert.equal(env.load().run(payload()), 'OK');
  env.files.get('id-1').sha256Checksum = digest('changed');
  assert.equal(env.load().run(payload()), 'ERROR');
  assert.equal(env.allocated(), 1);
});

test('el ejecutor del editor verifica pruebas con dobles y exige proyecto nuevo', () => {
  const env = harness({ fresh: true });
  assert.match(env.load().realChecks(), /^PASS: 10 checks/);
  assert.equal(env.props.has('0401:tokenHash'), false);
  assert.equal(env.files.size, 4);
  assert.throws(() => env.load().realChecks(), /fresh lab project/);
});
