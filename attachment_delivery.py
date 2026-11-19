"""Envio de adjuntos con confirmacion por sesion; NO reemplaza deduplicacion durable en servidor."""
import base64
import binascii
import hashlib
import json

MIMES = {"image/png", "image/jpeg", "image/webp", "application/pdf"}
MAX_FILES = 5
MAX_BYTES = 3 * 1024 * 1024

class AttachmentDeliveryError(Exception):
    pass

def fingerprint(item):
    if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
        raise AttachmentDeliveryError("Metadatos de archivo invalidos")
    if item.get("mime") not in MIMES:
        raise AttachmentDeliveryError("Tipo de archivo no permitido")
    try:
        raw = base64.b64decode(item["data"], validate=True)
    except (KeyError, TypeError, ValueError, binascii.Error):
        raise AttachmentDeliveryError("Contenido de archivo invalido") from None
    if len(raw) > MAX_BYTES:
        raise AttachmentDeliveryError("Archivo supera el maximo permitido")
    canonical = json.dumps([item["name"], item["mime"], hashlib.sha256(raw).hexdigest()], ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

def send_pending(submission_id, brand, files, acknowledgements, post, url, token):
    """Devuelve (confirmados,total). Un timeout sigue ambiguo sin idempotencia del servidor."""
    if not submission_id or not isinstance(submission_id, str):
        raise AttachmentDeliveryError("Identificador de envio invalido")
    if not isinstance(files, list) or len(files) > MAX_FILES:
        raise AttachmentDeliveryError("Cantidad de adjuntos invalida")
    keys = [fingerprint(item) for item in files]
    if len(keys) != len(set(keys)):
        raise AttachmentDeliveryError("Adjuntos duplicados en el envio")
    previous = acknowledgements.get(submission_id)
    if previous is None:
        previous = {"manifest": keys, "confirmed": []}
        acknowledgements[submission_id] = previous
    if previous["manifest"] != keys:
        raise AttachmentDeliveryError("El conjunto de adjuntos cambio despues de iniciar el envio")
    confirmed = set(previous["confirmed"])
    for item, key in zip(files, keys):
        if key in confirmed:
            continue
        response = post(url, json={"action": "attachments", "token": token, "submission_id": submission_id, "brand": brand, "files": [item], "attachment_key": key}, timeout=75)
        if response.status_code != 200 or response.text.strip() != "OK":
            raise AttachmentDeliveryError("El receptor no confirmo el adjunto")
        confirmed.add(key)
        previous["confirmed"].append(key)
    return len(confirmed), len(files)
