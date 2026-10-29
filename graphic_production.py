"""Puente Creative OS — hoja de producción gráfica controlada.

Produce especificaciones y encargos; no genera imágenes ni simula aprobaciones.
"""
import json
import re
from datetime import datetime, timezone
from review_workflow import validate_review

FORMAT_PRESETS={
    "instagram_post_4_5":{"label":"Publicación Instagram 4:5","width":1080,"height":1350,"medium":"estático"},
    "instagram_story_9_16":{"label":"Historia Instagram 9:16","width":1080,"height":1920,"medium":"estático"},
    "instagram_square_1_1":{"label":"Publicación cuadrada 1:1","width":1080,"height":1080,"medium":"estático"},
    "instagram_reel_9_16":{"label":"Reel vertical 9:16","width":1080,"height":1920,"medium":"video"},
}
PRODUCTION_VERSION="puente_production_0_1"
STATUS_DRAFT="borrador_bloqueado"
STATUS_APPROVED="habilitado_para_produccion"
STATE_LABELS={"idea":"Idea pendiente","en_diseno":"En diseño","revision":"En revisión","aprobada":"Aprobada","publicada":"Publicada"}

def _clean(value,length=2000):
    return str(value or "").strip()[:length]

def build_piece(submission_id,sequence,kind,title,objective,main_message,cta,
                visual_instructions="",source_assets="",copy_text=""):
    if kind not in FORMAT_PRESETS:
        raise ValueError("Formato de pieza no válido.")
    if not isinstance(sequence,int) or sequence<1 or sequence>30:
        raise ValueError("Número de pieza no válido.")
    return {
        "piece_id":str(submission_id)+"-p"+str(sequence).zfill(2),
        "orden":sequence,"formato_id":kind,
        "titulo":_clean(title,120),"objetivo":_clean(objective,500),
        "mensaje_principal":_clean(main_message,500),"cta":_clean(cta,240),
        "instrucciones_visuales":_clean(visual_instructions),
        "activos_fuente":_clean(source_assets,500),
        "copy":_clean(copy_text,3500),
        "estado":"idea",
        "revision_humana":False
    }

def validate_piece(piece):
    errors=[]
    if not isinstance(piece,dict):
        return ["La pieza no tiene una estructura válida."]
    if piece.get("formato_id") not in FORMAT_PRESETS:
        errors.append("Selecciona un formato válido.")
    for key,name in (("titulo","título"),("objetivo","objetivo"),("mensaje_principal","mensaje principal")):
        if len(_clean(piece.get(key)))<5:
            errors.append("Falta especificar "+name+".")
    if piece.get("estado") not in STATE_LABELS:
        errors.append("Estado de pieza desconocido.")
    return errors

def build_production_plan(record,review,audit,pieces,production_notes="",plan_id=None):
    """No inventar precio, entregables de contrato ni recursos autorizados."""
    sid=str(record.get("submission_id") or "")
    if not sid:
        raise ValueError("Falta el identificador del briefing.")
    if not isinstance(pieces,list) or len(pieces)>30:
        raise ValueError("Se admiten hasta 30 piezas por plan de producción.")
    ids=[item.get("piece_id") for item in pieces if isinstance(item,dict)]
    errors=[]
    if len(ids)!=len(pieces) or len(set(ids))!=len(ids) or any(not x or not x.startswith(sid+"-") for x in ids):
        errors.append("Los identificadores de las piezas son inválidos o están repetidos.")
    for i,item in enumerate(pieces,1):
        errors.extend("Pieza "+str(i)+": "+e for e in validate_piece(item))
    review_errors=validate_review(review,record,audit)
    human_approved=bool(not review_errors and review.get("autorizacion_produccion") is True)
    blocked=errors+review_errors
    if not human_approved and not review_errors:
        blocked.append("El director de arte todavía no autorizó producción.")
    direction=review.get("direccion_seleccionada") if human_approved else None
    return {
        "schema_version":PRODUCTION_VERSION,
        "submission_id":sid,
        "marca":_clean((record.get("answers") or {}).get("nombre"),120),
        "direccion_aprobada":direction,
        "responsable":_clean(review.get("responsable"),150),
        "estado":STATUS_APPROVED if human_approved and not errors else STATUS_DRAFT,
        "bloqueos":blocked,
        "piezas":pieces,
        "notas_produccion":_clean(production_notes),
        "plan_contratado":plan_id if plan_id in ("basico","ampliado","branding") else None,
        "nota_alcance":"La selección de un plan no valida el contrato. Los entregables deben cotejarse con la propuesta firmada.",
        "generated_at_utc":datetime.now(timezone.utc).isoformat()
    }

def production_prompt(plan,piece):
    """Un texto independiente por gráfica; nunca declarar assets inexistentes."""
    if plan.get("estado")!=STATUS_APPROVED:
        raise ValueError("La dirección de arte y la auditoría deben estar aprobadas antes de producir.")
    valid={p["piece_id"]:p for p in plan.get("piezas",[])}
    if piece.get("piece_id") not in valid:
        raise ValueError("La pieza no pertenece a este plan.")
    errors=validate_piece(piece)
    if errors:raise ValueError("; ".join(errors))
    preset=FORMAT_PRESETS[piece["formato_id"]]
    instructions=[
        "PUENTE CREATIVE OS — ENCARGO DE PRODUCCIÓN GRÁFICA",
        "Proyecto: "+plan["marca"],
        "Corriente madre aprobada: "+plan["direccion_aprobada"],
        "Pieza: "+piece["titulo"]+" · "+piece["piece_id"],
        "Formato exacto: "+str(preset["width"])+" × "+str(preset["height"])+" px · "+preset["label"],
        "Objetivo comunicacional: "+piece["objetivo"],
        "Mensaje principal: "+piece["mensaje_principal"],
        "Llamado a la acción: "+(piece["cta"] or "Por definir con el cliente"),
        "Instrucciones visuales aprobadas o por evaluar: "+(piece["instrucciones_visuales"] or "Sin definir"),
        "Recursos realmente disponibles: "+(piece["activos_fuente"] or "No se han confirmado archivos"),
        "Texto de acompañamiento: "+(piece["copy"] or "Por redactar"),
        "Indicaciones de dirección: "+(plan.get("notas_produccion") or "Sin notas adicionales"),
        "Respetar el logotipo real de la marca. No inventar logos ni datos de oferta.",
        "Confirmar licencias y autorizaciones de fotografías e ilustraciones.",
        "No inventar precios, horarios, promociones ni prestaciones.",
        "Respetar composición, jerarquía, legibilidad y formatos. Una gráfica por archivo.",
        "Requiere revisión humana antes de publicar; este encargo no equivale a una pieza final."
    ]
    return "\n".join(instructions)

def export_plan(plan):
    return json.dumps(plan,ensure_ascii=False,indent=2)
