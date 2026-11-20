const LAB = '0401:';
const MAX_BYTES = 3 * 1024 * 1024;
const MAX_FILES = 5;
const FILE_FIELDS = 'id,name,mimeType,sha256Checksum,parents,trashed';
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/;
const SHA256 = /^[0-9a-f]{64}$/;
const TYPES = {
  'application/pdf': [/\.pdf$/i, /^255044462d/],
  'image/png': [/\.png$/i, /^89504e470d0a1a0a/],
  'image/jpeg': [/\.jpe?g$/i, /^ffd8ff/],
  'image/webp': [/\.webp$/i, /^52494646........57454250/],
};

function doPost(event) {
  let result = 'INVALID';
  if (typeof event?.postData?.contents === 'string' &&
      event.postData.contents.length <= 4 * Math.ceil(MAX_BYTES / 3) + 4096) {
    let payload;
    try {
      payload = JSON.parse(event.postData.contents);
    } catch (_) {
      // Invalid JSON stays INVALID.
    }
    result = receiveAttachment_(payload);
  } else {
    audit_('invalid');
  }
  return ContentService.createTextOutput(result);
}

function sha256_(value) {
  const algorithm = Utilities.DigestAlgorithm.SHA_256;
  const digest = typeof value === 'string'
    ? Utilities.computeDigest(algorithm, value, Utilities.Charset.UTF_8)
    : Utilities.computeDigest(algorithm, value);
  return hex_(digest);
}

function hex_(bytes) {
  return Array.from(bytes, value => (value & 255).toString(16).padStart(2, '0')).join('');
}

function authorized_(token, expected) {
  if (typeof token !== 'string' || token.length < 32 || token.length > 256 ||
      !SHA256.test(expected || '')) return false;
  const actual = sha256_(token);
  let difference = 0;
  for (let i = 0; i < actual.length; i++) difference |= actual.charCodeAt(i) ^ expected.charCodeAt(i);
  return difference === 0;
}

function parseAttachment_(payload) {
  if (payload?.action !== 'attachments' || typeof payload.submission_id !== 'string' ||
      !UUID.test(payload.submission_id) || typeof payload.attachment_key !== 'string' ||
      !SHA256.test(payload.attachment_key) || !Array.isArray(payload.files) ||
      payload.files.length !== 1) return null;
  const { name, mime, data } = payload.files[0] || {};
  const type = typeof mime === 'string' && Object.prototype.hasOwnProperty.call(TYPES, mime) && TYPES[mime];
  if (!type || typeof name !== 'string' || !/^[\p{L}\p{N}][\p{L}\p{N}._ -]{0,99}$/u.test(name) ||
      !type[0].test(name) || typeof data !== 'string' || !data ||
      data.length > 4 * Math.ceil(MAX_BYTES / 3) || data.length % 4 ||
      /[^A-Za-z0-9+/=]/.test(data)) return null;
  let bytes;
  try {
    bytes = Utilities.base64Decode(data);
  } catch (_) {
    return null;
  }
  if (bytes.length > MAX_BYTES || Utilities.base64Encode(bytes) !== data ||
      !type[1].test(hex_(bytes.slice(0, 12)))) return null;
  const hash = sha256_(bytes);
  const key = sha256_(JSON.stringify([name, mime, hash]));
  if (key !== payload.attachment_key) return null;
  return { submission: payload.submission_id, key, hash, name, mime, bytes };
}

function audit_(event, operation) {
  // Only synthetic correlation identifiers and fixed event codes reach Cloud Logging.
  console.info({ message: 'puente.0401', event, ...(operation ? { operation } : {}) });
}

function ownerOnlyRoot_(id) {
  const folder = Drive.Files.get(id, { fields: 'id,mimeType,trashed,driveId' });
  if (folder.trashed || folder.driveId || folder.mimeType !== 'application/vnd.google-apps.folder') return false;
  return ownerOnlyPermissions_(id);
}

function ownerOnlyPermissions_(id) {
  const page = Drive.Permissions.list(id, { fields: 'nextPageToken,permissions(type,role)' });
  return !page.nextPageToken && page.permissions?.length === 1 &&
    page.permissions[0].role === 'owner' && page.permissions[0].type === 'user';
}

function receiveAttachment_(payload, afterWrite) {
  const properties = PropertiesService.getScriptProperties();
  if (!authorized_(payload?.token, properties.getProperty(LAB + 'tokenHash'))) {
    audit_('denied_auth');
    return 'DENIED';
  }
  const item = parseAttachment_(payload);
  if (!item) {
    audit_('invalid');
    return 'INVALID';
  }

  const lock = LockService.getScriptLock();
  if (!lock.tryLock(5000)) {
    audit_('busy');
    return 'RETRY';
  }
  let operation;
  try {
    const submission = LAB + 'submission:' + item.submission;
    const status = properties.getProperty(submission);
    if (status !== 'granted' ||
        !authorized_(payload.token, properties.getProperty(LAB + 'tokenHash'))) {
      audit_('denied_policy');
      return 'DENIED';
    }
    const root = properties.getProperty(LAB + 'root');
    if (!root || !ownerOnlyRoot_(root)) {
      audit_('denied_storage');
      return 'DENIED';
    }

    const prefix = LAB + 'file:' + item.submission + ':';
    const recordKey = prefix + item.key;
    const existing = properties.getProperty(recordKey);
    let record;
    if (existing) {
      record = JSON.parse(existing);
      operation = record.operation;
      if (record.hash !== item.hash || record.root !== root ||
          !['PENDING', 'CONFIRMED'].includes(record.state)) {
        audit_('conflict', operation);
        return 'ERROR';
      }
    } else {
      if (properties.getKeys().filter(key => key.startsWith(prefix)).length >= MAX_FILES) {
        audit_('limit');
        return 'INVALID';
      }
      const fileId = Drive.Files.generateIds({ count: 1, space: 'drive' }).ids?.[0];
      if (!fileId) throw new Error('ID allocation failed');
      operation = Utilities.getUuid();
      record = { state: 'PENDING', operation, fileId, root, hash: item.hash, createdAt: new Date().toISOString() };
      properties.setProperty(recordKey, JSON.stringify(record));
      audit_('pending', operation);
    }

    let stored;
    if (existing && record.state === 'PENDING') {
      try {
        stored = Drive.Files.get(record.fileId, { fields: FILE_FIELDS });
      } catch (_) {
        // The read may also be ambiguous. Reusing the reserved ID still prevents duplicates.
      }
    }
    if (record.state === 'PENDING' && !stored) {
      try {
        // Drive guarantees uniqueness of a generated ID. Every retry uses the reserved ID.
        Drive.Files.create({
          id: record.fileId, name: item.name, mimeType: item.mime, parents: [root],
        }, Utilities.newBlob(item.bytes, item.mime, item.name), { fields: 'id' });
      } catch (_) {
        // An ambiguous create or a conflict is resolved by reading the same ID below.
        audit_('create_uncertain', operation);
      }
      if (afterWrite) afterWrite();
    }
    if (!stored) stored = Drive.Files.get(record.fileId, { fields: FILE_FIELDS });
    if (stored.id !== record.fileId || stored.trashed || stored.name !== item.name ||
        stored.mimeType !== item.mime || stored.sha256Checksum !== item.hash ||
        stored.parents?.length !== 1 || stored.parents[0] !== root ||
        !ownerOnlyPermissions_(record.fileId)) {
      audit_('conflict', operation);
      return 'ERROR';
    }
    if (record.state === 'PENDING') {
      properties.setProperty(recordKey, JSON.stringify({
        ...record, state: 'CONFIRMED', confirmedAt: new Date().toISOString(),
      }));
      audit_(existing ? 'reconciled' : 'confirmed', operation);
    } else {
      audit_('replayed', operation);
    }
    return 'OK';
  } catch (_) {
    audit_('retry', operation);
    return 'RETRY';
  } finally {
    lock.releaseLock();
  }
}
