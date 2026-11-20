// Editor-only entry point for a fresh lab project. Never called by doPost.
function runSyntheticLab0401() {
  const props = PropertiesService.getScriptProperties();
  const lock = LockService.getScriptLock();
  lock.waitLock(5000);
  const token = Utilities.getUuid() + Utilities.getUuid();
  const tokenKey = LAB + 'tokenHash';
  const rootKey = LAB + 'root';
  const first = Utilities.getUuid();
  const second = Utilities.getUuid();
  let folder;
  try {
    if (props.getKeys().some(key => key.startsWith(LAB))) {
      throw new Error('Run requires a fresh lab project');
    }
    folder = Drive.Files.create({
      name: 'PUENTE 04.01 · laboratorio sintético',
      mimeType: 'application/vnd.google-apps.folder',
    }, null, { fields: 'id' }).id;
    props.setProperties({
      [rootKey]: folder,
      [tokenKey]: sha256_(token),
      [LAB + 'submission:' + first]: 'granted',
      [LAB + 'submission:' + second]: 'granted',
    });
  } finally {
    lock.releaseLock();
  }

  const make = (id, name) => {
    const mime = 'application/pdf';
    const body = '%PDF-1.4\n% PUENTE 04.01 synthetic fixture\n%%EOF\n';
    return {
      action: 'attachments', token, submission_id: id,
      attachment_key: sha256_(JSON.stringify([name, mime, sha256_(body)])),
      files: [{ name, mime, data: Utilities.base64Encode(body, Utilities.Charset.UTF_8) }],
    };
  };
  const verify = (value, expected, name) => {
    if (value !== expected) throw new Error(name + ': expected ' + expected + ', got ' + value);
    audit_('test_pass_' + name);
  };
  const run = payload => doPost({ postData: { contents: JSON.stringify(payload) } }).getContent();
  try {
    const primary = make(first, 'fixture.pdf');
    const interrupted = make(first, 'interrupted.pdf');
    verify(run({ ...primary, token: 'invalid' }), 'DENIED', 'auth');
    verify(run({ ...primary, submission_id: Utilities.getUuid(), files_consent: true }), 'DENIED', 'consent');
    verify(run({ ...primary, files: [{ ...primary.files[0], data: 'abcd' }] }), 'INVALID', 'content');
    verify(run(primary), 'OK', 'first_write');
    verify(run(primary), 'OK', 'replay');
    verify(receiveAttachment_(interrupted, () => { throw new Error('Synthetic interruption'); }),
      'RETRY', 'interrupted_after_write');
    verify(run(interrupted), 'OK', 'recovered');
    verify(run(make(second, 'fixture.pdf')), 'OK', 'independent_submission');
    lock.waitLock(5000);
    try {
      props.setProperty(LAB + 'submission:' + first, 'revoked');
    } finally {
      lock.releaseLock();
    }
    verify(run(primary), 'DENIED', 'revoked_replay');
    const page = Drive.Files.list({
      q: "'" + folder + "' in parents and trashed = false",
      fields: 'nextPageToken,files(id)',
    });
    verify(!page.nextPageToken && page.files?.length, 3, 'drive_file_count');
    return 'PASS: 10 checks; see execution logs';
  } finally {
    lock.waitLock(5000);
    try {
      props.deleteProperty(tokenKey);
    } finally {
      lock.releaseLock();
    }
  }
}
