/**
 * PUENTE Creative OS Beta 0.2 — receptor para Google Sheets.
 * Crear desde Extensiones > Apps Script en la hoja de destino.
 * Propiedad de script requerida: WEBHOOK_TOKEN = valor secreto aleatorio.
 * Implementar como aplicación web: ejecutar como propietario; acceso: cualquiera.
 * No publicar el token en GitHub.
 */
function doPost(e) {
  const lock = LockService.getScriptLock();
  try {
    const payload = JSON.parse((e && e.postData && e.postData.contents) || '{}');
    const expected = PropertiesService.getScriptProperties().getProperty('WEBHOOK_TOKEN');
    if (!expected || !payload.token || payload.token !== expected) {
      return ContentService.createTextOutput('DENIED');
    }
    const record = payload.record || {};
    if (!record.submission_id || !record.answers || !record.diagnostic) {
      return ContentService.createTextOutput('INVALID');
    }
    lock.waitLock(15000);
    const book = SpreadsheetApp.getActiveSpreadsheet();
    let sheet = book.getSheetByName('Respuestas');
    if (!sheet) sheet = book.insertSheet('Respuestas');
    if (sheet.getLastRow() === 0) {
      sheet.appendRow(['fecha_utc','submission_id','marca','actividad','estado','suficiencia','objetivo','canales','respuestas_json','diagnostico_json']);
      sheet.setFrozenRows(1);
    }
    const id = String(record.submission_id);
    const ids = sheet.getLastRow() > 1 ? sheet.getRange(2,2,sheet.getLastRow()-1,1).getValues() : [];
    if (!ids.some(row => String(row[0]) === id)) {
      const a = record.answers;
      const d = record.diagnostic;
      // Prefixed fields guard against formula injection when copied to cells.
      const safe = v => "'" + String(v == null ? '' : v).slice(0,10000);
      sheet.appendRow([
        safe(record.submitted_at),safe(id),safe(a.nombre),safe(a.negocio),
        safe(d.status),Number(d.score)||0,safe(a.objetivo),
        safe((a.canales||[]).join(', ')),
        JSON.stringify(a),JSON.stringify(d)
      ]);
    }
    return ContentService.createTextOutput('OK');
  } catch (err) {
    return ContentService.createTextOutput('ERROR');
  } finally {
    if (lock.hasLock()) lock.releaseLock();
  }
}