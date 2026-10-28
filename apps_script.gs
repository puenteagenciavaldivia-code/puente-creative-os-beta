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
    if (['clarify_create','clarify_list','clarify_fetch','clarify_submit','clarify_send_email'].includes(payload.action)) {
      return clarificationRoute(payload);
    }
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


/**
 * Beta 1.0 — aclaraciones seguras con tokens opacos y expiración.
 * Requiere nueva propiedad CLARIFICATIONS_ADMIN_TOKEN y redeploy.
 * Ruta pública sin acceso a la hoja Respuestas (solo preguntas seleccionadas).
 */
const CLARIFY_TAB='Aclaraciones';
const CLARIFY_HEADERS=['created_at_utc','submission_id','marca','token_sha256','expires_at_utc','questions_json','answers_json','status','responded_at_utc','email_sent_at_utc'];
function clarifySheet() {
  const book=SpreadsheetApp.openById(SPREADSHEET_ID);
  let sheet=book.getSheetByName(CLARIFY_TAB);
  if (!sheet) sheet=book.insertSheet(CLARIFY_TAB);
  if (sheet.getLastRow()===0) { sheet.appendRow(CLARIFY_HEADERS); sheet.setFrozenRows(1); }
  return sheet;
}
function hashToken(t) {
  const d=Utilities.computeDigest(Utilities.DigestAlgorithm.SHA_256,String(t),Utilities.Charset.UTF_8);
  return d.map(v=>('0'+(v<0?v+256:v).toString(16)).slice(-2)).join('');
}
function jsonReply(o) {return reply(JSON.stringify(o));}
function adminClarifyAllowed(p) {
  const token=PropertiesService.getScriptProperties().getProperty('CLARIFICATIONS_ADMIN_TOKEN');
  return !!(token && p.admin_token && p.admin_token===token);
}
function rowForClarification(sheet,token) {
  const hash=hashToken(token);
  const last=sheet.getLastRow();
  if(last<2)return 0;
  const values=sheet.getRange(2,4,last-1,1).getDisplayValues();
  const idx=values.findIndex(r=>r[0]===hash);
  return idx<0?0:idx+2;
}
function clarificationRoute(p) {
  const action=p.action;
  const isAdmin=['clarify_create','clarify_list','clarify_send_email'].includes(action);
  if (isAdmin && !adminClarifyAllowed(p)) return reply('DENIED');
  if (!isAdmin && (typeof p.access_token!=='string' || !/^[a-f0-9]{64}$/.test(p.access_token)))return reply('DENIED');
  const lock=LockService.getScriptLock();
  try {
    lock.waitLock(15000);
    const sheet=clarifySheet();
    if(action==='clarify_create') {
      const id=String(p.submission_id||'');
      const brand=String(p.brand||'').slice(0,120);
      const questions=p.questions;
      if(!/^[a-f0-9-]{36}$/i.test(id)||!Array.isArray(questions)||questions.length<1||questions.length>12)return reply('INVALID');
      const ids=new Set();
      for(const q of questions){
        if(typeof q.id!=='string'||!/^[a-z_]{2,40}$/.test(q.id)||ids.has(q.id)
        ||typeof q.pregunta!=='string'||!q.pregunta.trim()||q.pregunta.length>450)return reply('INVALID');
        ids.add(q.id);
      }
      const brief=SpreadsheetApp.openById(SPREADSHEET_ID).getSheetByName('Respuestas');
      if(!brief||!findSubmission(brief,id))return reply('INVALID');
      // Token originates from server-side Streamlit secrets/CSPRNG, not a client ID.
      const token=String(p.access_token||'');
      if(!/^[a-f0-9]{64}$/.test(token))return reply('INVALID');
      if(rowForClarification(sheet,token))return reply('INVALID');
      const expiry=new Date(Date.now()+7*86400000).toISOString();
      sheet.appendRow([new Date().toISOString(),safe(id),safe(brand),hashToken(token),expiry,
        JSON.stringify(questions),'','pending','','']);
      return jsonReply({ok:true,expires_at_utc:expiry});
    }
    if(action==='clarify_list') {
      const last=sheet.getLastRow();if(last<2)return jsonReply({ok:true,items:[]});
      const start=Math.max(2,last-149);
      const rows=sheet.getRange(start,1,last-start+1,10).getDisplayValues();
      const items=rows.reverse().map(r=>{
        let questions=[],answers=[];
        try{questions=JSON.parse(r[5]||'[]')}catch(e){}
        try{answers=JSON.parse(r[6]||'[]')}catch(e){}
        return {created_at_utc:r[0],submission_id:r[1].replace(/^'/,''),
          brand:r[2].replace(/^'/,''),expires_at_utc:r[4],questions:questions,
          answers:answers,status:r[7],responded_at_utc:r[8],email_sent_at_utc:r[9]};
      });
      return jsonReply({ok:true,items:items});
    }
    const row=rowForClarification(sheet,p.access_token);
    if(!row)return reply('DENIED');
    const cells=sheet.getRange(row,1,1,10).getDisplayValues()[0];
    const expired=Date.now()>=new Date(cells[4]).getTime();
    if(expired)return reply('EXPIRED');
    if(action==='clarify_fetch') {
      if(cells[7]!=='pending')return reply('CLOSED');
      return jsonReply({ok:true,brand:cells[2].replace(/^'/,''),questions:JSON.parse(cells[5]),expires_at_utc:cells[4]});
    }
    if(action==='clarify_submit') {
      if(cells[7]!=='pending')return reply('CLOSED');
      const received=p.answers;
      const questions=JSON.parse(cells[5]);
      if(!Array.isArray(received)||received.length!==questions.length)return reply('INVALID');
      for(let i=0;i<questions.length;i++){
        const r=received[i];
        if(!r||r.id!==questions[i].id||typeof r.respuesta!=='string'||!r.respuesta.trim()
            ||r.respuesta.length>4000)return reply('INVALID');
      }
      sheet.getRange(row,7,1,3).setValues([[JSON.stringify(received),'received_unverified',new Date().toISOString()]]);
      return jsonReply({ok:true,status:'received_unverified'});
    }
    return reply('INVALID');
  }catch(err){console.error(err);return reply('ERROR');}
  finally{if(lock.hasLock())lock.releaseLock();}
}
