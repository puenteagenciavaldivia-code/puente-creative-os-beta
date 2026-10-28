"""Validación manual de una ficha estratégica, sin aprobar por algoritmo."""
import copy
from datetime import datetime, timezone

ALLOWED_STATES={"pendiente","confirmado","aclarar","descartado"}
DIRECTIONS_MIN=2
DIRECTIONS_MAX=3

def new_review(record,audit):
    return {
        "schema_version":"puente_review_0_8",
        "submission_id":str(record.get("submission_id") or ""),
        "marca":str((record.get("answers") or {}).get("nombre") or ""),
        "revision":{},
        "corrientes":[],
        "direccion_seleccionada":None,
        "observaciones":"",
        "responsable":"",
        "revision_completada":False,
        "autorizacion_produccion":False,
        "audit_ids":[str(item.get("id","")) for item in audit.get("preguntas_priorizadas",[])],
        "updated_at_utc":None,
    }

def _audit_id_set(audit):
    return {str(item.get("id","")) for item in audit.get("preguntas_priorizadas",[])}

def validate_review(review,record,audit):
    """Retorna errores concretos. No modifica fuentes ni decide por el equipo."""
    if not isinstance(review,dict):
        return ["El archivo de revisión debe contener un objeto."]
    errors=[]
    sid=str(record.get("submission_id") or "")
    if not sid or str(review.get("submission_id"))!=sid:
        errors.append("El documento no corresponde al briefing seleccionado.")
    if review.get("schema_version")!="puente_review_0_8":
        errors.append("Versión de revisión no compatible.")
    ids=_audit_id_set(audit)
    decisions=review.get("revision")
    if not isinstance(decisions,dict):
        decisions={}
        errors.append("La revisión de preguntas no es válida.")
    for key in ids:
        item=decisions.get(key)
        state=item.get("estado") if isinstance(item,dict) else None
        if state not in ALLOWED_STATES - {"pendiente"}:
            errors.append("Falta resolver la pregunta: "+key)
        if state in ("confirmado","descartado"):
            note=(item.get("nota") or "").strip() if isinstance(item,dict) else ""
            if len(note)<8:
                errors.append("Explica con al menos ocho caracteres la decisión: "+key)
    unknown=set(decisions)-ids
    if unknown:
        errors.append("Hay preguntas ajenas a este briefing: "+", ".join(sorted(unknown)))
    if not str(review.get("responsable") or "").strip():
        errors.append("Identifica a la persona que realiza la revisión.")
    currents=review.get("corrientes")
    if not isinstance(currents,list):
        currents=[]
        errors.append("Las propuestas creativas deben ser una lista.")
    if not DIRECTIONS_MIN<=len(currents)<=DIRECTIONS_MAX:
        errors.append("Documenta dos o tres corrientes madre alternativas antes de seleccionar.")
    seen=set()
    for i,entry in enumerate(currents,1):
        if not isinstance(entry,dict):
            errors.append("La corriente "+str(i)+" no tiene una estructura válida.")
            continue
        name=str(entry.get("nombre") or "").strip()
        if not name:
            errors.append("Falta el nombre de la corriente "+str(i))
        elif name.casefold() in seen:
            errors.append("No repitas la misma corriente madre.")
        else:
            seen.add(name.casefold())
        for key,label in (("fundamento","fundamento"),("riesgos","riesgos"),("diferenciacion","diferenciación respecto de otras propuestas")):
            if len(str(entry.get(key) or "").strip())<15:
                errors.append("Completa "+label+" de la corriente "+str(i))
    chosen=review.get("direccion_seleccionada")
    if chosen and str(chosen).casefold() not in seen:
        errors.append("La dirección seleccionada debe coincidir con una de las corrientes comparadas.")
    if not chosen:
        errors.append("Todavía no se ha seleccionado una corriente madre.")
    if not str(review.get("observaciones") or "").strip():
        errors.append("Escribe una justificación editorial para la selección.")
    if any(isinstance(item,dict) and item.get("estado")=="aclarar" for item in decisions.values()):
        errors.append("Existen preguntas pendientes de aclaración con el cliente.")
    return errors

def prepare_reviewed_package(handoff,review,audit):
    """Produce un paquete exportable; no cambia el briefing ni escribe en Sheets."""
    record={"submission_id":handoff.get("submission_id"),"answers":handoff.get("respuestas_originales")}
    errors=validate_review(review,record,audit)
    result=copy.deepcopy(handoff)
    result["revision_editorial"]=copy.deepcopy(review)
    result["bloqueos_de_produccion"]=errors
    result["listo_para_revision_final"]=not errors
    result["aprobado_para_produccion"]=bool(not errors and review.get("autorizacion_produccion"))
    result["revision_generada_utc"]=datetime.now(timezone.utc).isoformat()
    if result["aprobado_para_produccion"]:
        result["decisiones_creativas"]["corriente_madre"]=review["direccion_seleccionada"]
        result["decisiones_creativas"]["aprobacion_humana"]=True
    return result
