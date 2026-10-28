/**
 * PUENTE Creative OS Beta 0.3 — receptor de briefings y adjuntos.
 * Proyecto independiente de Apps Script. Mantener WEBHOOK_TOKEN privado.
 * Tras pegar: Guardar > Implementar > Administrar implementaciones > Editar > Nueva versión.
 * Los adjuntos se guardan en Drive privado del propietario; enlaces en la hoja Respuestas.
 */
const SPREADSHEET_ID = '1B79PdKG0cCWlp3bsa1WtihMCDQbCRFJcxd6W2AaQ9NM';
const ROOT_FOLDER_NAME = 'PUENTE Creative OS — Adjuntos';
const ALLOWED_MIME = ['image/png','image/jpeg','image/webp','application/pdf'];
function reply(s) { return ContentService.createTextOutput(s); }
function safe(v) { return "'" + String(v == null ? '' : v).slice(0,10000); }
function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const payload = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    if (payload.action === 'admin_list') return adminList(payload);
    const token = PropertiesService.getScriptProperties().getProperty('WEBHOOK_TOKEN');
    if (!token || !payload.token || payload.token !== token) return reply('DENIED');
    lock.waitLock(20000);
    const book = SpreadsheetApp.openById(SPREADSHEET_ID);
    let sheet = book.getSheetByName('Respuestas');
    if (!sheet) sheet = book.insertSheet('Respuestas');
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['fecha_utc','submission_id','marca','actividad','estado','suficiencia','objetivo','canales','respuestas_json','diagnostico_json','adjuntos_drive']);
      sheet.setFrozenRows(1);
    }
    if (sheet.getRange(1,11).getValue() !== 'adjuntos_drive') sheet.getRange(1,11).setValue('adjuntos_drive');
    if (payload.action === 'attachments') return saveAttachments(payload,sheet);
    const record = payload.record || {};
    if (!record.submission_id || !record.answers || !record.diagnostic) return reply('INVALID');
    const id = String(record.submission_id);
    const row = findSubmission(sheet,id);
    if (!row) {
      const a=record.answers,d=record.diagnostic;
      sheet.appendRow([safe(record.submitted_at),safe(id),safe(a.nombre),safe(a.negocio),
        safe(d.status),Number(d.score)||0,safe(a.objetivo),
        safe((a.canales||[]).join(', ')),JSON.stringify(a),JSON.stringify(d),'']);
    }
    return reply('OK');
  } catch (err) {
    console.error(err);
    return reply('ERROR');
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}
function findSubmission(sheet,id) {
  const n=sheet.getLastRow();
  if (n<2) return 0;
  const vals=sheet.getRange(2,2,n-1,1).getDisplayValues();
  const idx=vals.findIndex(r=>String(r[0]).replace(/^'/,'')===id);
  return idx<0 ? 0 : idx+2;
}
function cleanName(s) {
  return String(s||'archivo').replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚñÑ._ -]/g,'_').slice(0,100);
}
function saveAttachments(payload,sheet) {
  const id=String(payload.submission_id||'');
  const row=findSubmission(sheet,id);
  if (!row || !/^[a-f0-9-]{36}$/i.test(id)) return reply('INVALID');
  const files=payload.files||[];
  if (!Array.isArray(files) || files.length!==1) return reply('INVALID');
  const file=files[0];
  const name=cleanName(file.name);
  const mime=String(file.mime||'');
  if (!ALLOWED_MIME.includes(mime) || !/\.(png|jpe?g|webp|pdf)$/i.test(name)) return reply('INVALID');
  if (typeof file.data!=='string' || file.data.length>4200000) return reply('INVALID');
  const bytes=Utilities.base64Decode(file.data);
  if (bytes.length>3*1024*1024) return reply('INVALID');
  const rootIterator=DriveApp.getFoldersByName(ROOT_FOLDER_NAME);
  const root=rootIterator.hasNext()?rootIterator.next():DriveApp.createFolder(ROOT_FOLDER_NAME);
  const folderName=id;
  const existing=root.getFoldersByName(folderName);
  const folder=existing.hasNext()?existing.next():root.createFolder(folderName);
  // Retry-safe: same file name in same submission is not uploaded twice.
  const matches=folder.getFilesByName(name);
  const saved=matches.hasNext()?matches.next():folder.createFile(Utilities.newBlob(bytes,mime,name));
  const link=saved.getUrl();
  const old=String(sheet.getRange(row,11).getValue()||'');
  if (!old.includes(link)) sheet.getRange(row,11).setValue(old ? old+'\n'+link : link);
  return reply('OK');
}

/**
 * Ejecutar manualmente una sola vez desde el editor de Apps Script.
 * Solicita los permisos necesarios y verifica Sheets + Drive.
 * No publica enlaces ni altera briefings anteriores.
 */
function verificarAccesoDrive() {
  const sheet = SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('Respuestas');
  if (!sheet) throw new Error('No se encontró la pestaña Respuestas.');
  const folders = DriveApp.getFoldersByName(ROOT_FOLDER_NAME);
  const folder = folders.hasNext() ? folders.next() : DriveApp.createFolder(ROOT_FOLDER_NAME);
  console.log('Acceso a Google Sheets y Drive confirmado. Carpeta ID: ' + folder.getId());
  return 'OK';
}

/**
 * Lectura exclusiva para el panel interno.
 * Usar ADMIN_READ_TOKEN distinto de WEBHOOK_TOKEN.
 */
function adminList(payload) {
  const expected=PropertiesService.getScriptProperties().getProperty('ADMIN_READ_TOKEN');
  if (!expected || !payload.admin_token || payload.admin_token !== expected) return reply('DENIED');
  const book=SpreadsheetApp.openById(SPREADSHEET_ID);
  const sheet=book.getSheetByName('Respuestas');
  if (!sheet || sheet.getLastRow()<2) return reply(JSON.stringify({items:[]}));
  const last=sheet.getLastRow();
  const start=Math.max(2,last-99);
  const data=sheet.getRange(start,1,last-start+1,11).getDisplayValues();
  const items=data.reverse().map(row=>{
    let answers={},diagnostic={};
    try { answers=JSON.parse(row[8]||'{}'); } catch(e) {}
    try { diagnostic=JSON.parse(row[9]||'{}'); } catch(e) {}
    return {
      submitted_at:row[0].replace(/^'/,''),
      submission_id:row[1].replace(/^'/,''),
      brand:row[2].replace(/^'/,''),
      business:row[3].replace(/^'/,''),
      status:row[4].replace(/^'/,''),
      score:Number(row[5])||0,
      answers:answers,
      diagnostic:diagnostic,
      attachments:(row[10]||'').split(/\n/).filter(x=>x.startsWith('https://drive.google.com/'))
    };
  });
  return reply(JSON.stringify({items:items}));
}
