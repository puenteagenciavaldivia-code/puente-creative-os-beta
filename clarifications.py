"""Mini fichas complementarias: intercambio manual y trazable en beta.

No persiste datos ni envía al receptor hasta que exista un backend seguro.
"""
import copy
from datetime import datetime, timezone

REQUEST_VERSION="puente_clarifications_request_0_1"
REPLY_VERSION="puente_clarifications_reply_0_1"

def build_request(record,audit,selected_ids):
    if not record.get("submission_id"):
        raise ValueError("El briefing no tiene identificador.")
    questions=[q for q in audit.get("preguntas_priorizadas",[])
               if q.get("id") in set(selected_ids)]
    if not questions:
        raise ValueError("Selecciona al menos una pregunta.")
    if len(questions)>12:
        raise ValueError("Envia máximo doce preguntas por ficha.")
    return {
        "schema_version":REQUEST_VERSION,
        "submission_id":record["submission_id"],
        "marca":str((record.get("answers") or {}).get("nombre") or ""),
        "instrucciones":"Ayúdanos respondiendo solo estas preguntas, con tus palabras. Si algo no está definido, indícalo.",
        "preguntas":[{"id":q["id"],"pregunta":q["pregunta"],"area":q.get("area","")}
                     for q in questions],
        "created_at_utc":datetime.now(timezone.utc).isoformat()
    }

def validate_request(payload):
    if not isinstance(payload,dict) or payload.get("schema_version")!=REQUEST_VERSION:
        raise ValueError("Ficha de aclaraciones incompatible.")
    if not str(payload.get("submission_id") or "").strip():
        raise ValueError("La ficha no tiene identificador.")
    questions=payload.get("preguntas")
    if not isinstance(questions,list) or not 1<=len(questions)<=12:
        raise ValueError("La ficha debe incluir entre una y doce preguntas.")
    ids=[q.get("id") for q in questions if isinstance(q,dict)]
    if len(ids)!=len(questions) or len(ids)!=len(set(ids)):
        raise ValueError("Las preguntas deben tener identificadores únicos.")
    if not all(isinstance(q.get("pregunta"),str) and q["pregunta"].strip() for q in questions):
        raise ValueError("Hay preguntas sin texto.")
    return payload

def build_reply(request,answers):
    validate_request(request)
    allowed={x["id"] for x in request["preguntas"]}
    if set(answers)-allowed:
        raise ValueError("Hay respuestas ajenas a esta ficha.")
    return {
        "schema_version":REPLY_VERSION,
        "submission_id":request["submission_id"],
        "marca":request.get("marca",""),
        "respuestas":[{"id":x["id"],"pregunta":x["pregunta"],
                       "respuesta":str(answers.get(x["id"],"")).strip()}
                      for x in request["preguntas"]],
        "responded_at_utc":datetime.now(timezone.utc).isoformat(),
        "estado":"recibido_sin_verificar",
    }

def validate_reply(reply,record,audit):
    if not isinstance(reply,dict) or reply.get("schema_version")!=REPLY_VERSION:
        raise ValueError("Archivo de respuestas incompatible.")
    if reply.get("submission_id")!=record.get("submission_id"):
        raise ValueError("Las aclaraciones no pertenecen al briefing seleccionado.")
    known={x["id"] for x in audit.get("preguntas_priorizadas",[])}
    rows=reply.get("respuestas")
    if not isinstance(rows,list) or not rows:
        raise ValueError("No hay respuestas.")
    ids=[row.get("id") for row in rows if isinstance(row,dict)]
    if len(ids)!=len(rows) or len(set(ids))!=len(ids) or not set(ids)<=known:
        raise ValueError("Las respuestas no corresponden a las preguntas de la auditoría.")
    if any(len(str(row.get("respuesta") or ""))>4000 for row in rows):
        raise ValueError("Una respuesta supera el máximo de 4000 caracteres.")
    return reply

def attach_reply(review,reply,record,audit):
    validate_reply(reply,record,audit)
    result=copy.deepcopy(review)
    result["aclaraciones_cliente"]={
        "estado":"recibido_sin_verificar",
        "respuestas":reply["respuestas"],
        "responded_at_utc":reply.get("responded_at_utc")
    }
    # No marcar preguntas como confirmadas automáticamente.
    return result
