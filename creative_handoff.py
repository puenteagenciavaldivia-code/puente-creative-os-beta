"""Traspaso estructurado del briefing para el equipo creativo de Puente."""
GROUPS = {
    "identidad": ("nombre", "negocio", "personalidad", "recuerdo"),
    "oferta": ("productos", "diferencia", "destacar", "competencia"),
    "audiencia": ("publico", "publico_nuevo", "dudas", "tono"),
    "visual": ("identidad_visual", "elementos", "referentes", "evitar", "autorizacion"),
    "comunicacion": ("objetivo", "accion", "canales"),
    "produccion": ("materiales", "condiciones"),
}
REQUIREMENTS = {
    "estrategia_de_marca": ("negocio", "productos", "diferencia", "publico"),
    "plan_de_contenidos": ("objetivo", "canales", "publico", "materiales"),
    "exploracion_de_corrientes_madre": ("personalidad", "publico", "referentes", "evitar", "elementos"),
    "planificacion_de_produccion": ("materiales", "condiciones", "accion"),
}
def _filled(value):
    return bool(value) and str(value).strip() not in ("", "Selecciona una opción")

def build_handoff(record):
    """Preserva las respuestas originales y no inventa recomendaciones de diseño."""
    answers = record.get("answers") or {}
    if not isinstance(answers, dict):
        raise ValueError("Respuestas no válidas")
    diagnostic = record.get("diagnostic") or {}
    quality = diagnostic.get("field_quality") or {}
    blocks = {
        name: {
            "declaraciones_del_cliente": {key: answers[key] for key in fields if _filled(answers.get(key))},
            "por_consultar": [key for key in fields if not _filled(answers.get(key))],
        }
        for name, fields in GROUPS.items()
    }
    readiness = {}
    for task, fields in REQUIREMENTS.items():
        gaps = [key for key in fields if not _filled(answers.get(key)) or quality.get(key, 0) < 0.75]
        readiness[task] = {
            "informacion_pendiente": gaps,
            "requiere_revision_humana": True,
            "diagnostico_verificado": False,
            "aprobado": False,
        }
    return {
        "schema_version": "puente_creative_handoff_0_1",
        "source": "briefing_cliente",
        "submission_id": record.get("submission_id"),
        "marca": answers.get("nombre", ""),
        "respuestas_originales": answers,
        "bloques": blocks,
        "preparacion": readiness,
        "alertas": diagnostic.get("flags", []),
        "auditoria_estrategica": diagnostic.get("strategic_audit"),
        "preguntas_pendientes": diagnostic.get("follow_up_questions", []),
        "adjuntos": record.get("attachments", []),
        "hipotesis_por_explorar": [],
        "decisiones_creativas": {
            "corriente_madre": None,
            "arquetipo": None,
            "concepto": None,
            "direccion_fotografica": None,
            "aprobacion_humana": False,
        },
        "advertencia": "Ficha de organización: no interpreta semántica ni aprueba decisiones creativas.",
    }
