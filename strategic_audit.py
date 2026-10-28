"""Auditoría preliminar automática de preparación creativa (reglas, sin IA).

Todas las preguntas son propuestas de validación interna, no afirmaciones de que
un dato no exista. No inventar hechos, ni seleccionar corrientes madre.
"""
import re
import unicodedata

def _norm(value):
    if isinstance(value,list):
        value=" ".join(map(str,value))
    text=unicodedata.normalize("NFKD",str(value or "").lower())
    return "".join(c for c in text if not unicodedata.combining(c))

def _has(text,patterns):
    return any(re.search(p,text) for p in patterns)

def audit_briefing(answers,diagnostic=None):
    if not isinstance(answers,dict):
        raise ValueError("Respuestas inválidas")
    diagnostic=diagnostic or {}
    text=" ".join(_norm(answers.get(k)) for k in ("negocio","productos","destacar","publico","condiciones"))
    product=_norm(answers.get("productos"))
    constraints=_norm(answers.get("condiciones"))
    goal=_norm(answers.get("objetivo"))
    audience=_norm(answers.get("publico"))
    materials=_norm(answers.get("materiales"))
    questions=[]
    def add(code,area,question,reason,priority="media",source_fields=None):
        questions.append({"id":code,"area":area,"pregunta":question,
                          "motivo":reason,"prioridad":priority,
                          "campos_origen":source_fields or []})
    # Independientes del rubro: preguntas explícitas que el briefing todavía no recoge.
    if not _has(product, [r"\$\s*\d",r"\bprecios?\b",r"\btarifas?\b",r"\bvalor(?:es)?\b"]):
        add("precios","Oferta","¿Cuáles son los precios, rangos de tarifa o condiciones comerciales principales?",
            "Los precios y condiciones de venta no se solicitan expresamente en el formulario.",
            "alta",["productos"])
    if not _has(constraints+" "+product,[r"reserv",r"pedido",r"compra",r"cotiz",r"whatsapp",r"agend",r"web"]):
        add("conversion","Conversión","¿Cómo realiza una persona la consulta, reserva o compra, paso a paso?",
            "El recorrido desde la publicación hasta la conversión requiere confirmación.",
            "alta",["objetivo","accion","condiciones"])
    if not _has(constraints,[r"meta",r"objetiv[oa] numer",r"\b\d+\s*(?:reserv|consulta|venta|cliente)",r"indicador",r"conversion"]):
        add("indicador","Resultados","¿Qué resultado medible definiría el éxito de la campaña?",
            "El objetivo indicado no establece una meta cuantificable.",
            "media",["objetivo","condiciones"])
    if not _has(materials,[r"autorizad",r"licenci",r"permiso",r"derechos",r"cesion"]):
        add("permisos","Producción","¿Qué fotografías, videos, testimonios y logotipos están autorizados para publicar?",
            "La disponibilidad declarada de material no demuestra derechos o autorización de publicación.",
            "alta",["materiales","autorizacion"])
    if not _has(constraints,[r"presupuesto",r"\$\s*\d",r"inversi[oó]n",r"pauta"]):
        add("presupuesto","Producción","¿Hay un presupuesto previsto para producción y publicidad pagada?",
            "El alcance de la campaña depende de recursos no consultados de forma directa.",
            "media",["condiciones"])
    if not audience.strip():
        add("publico","Audiencia","¿Quiénes compran y qué necesitan resolver?",
            "La audiencia es central para definir mensajes.","alta",["publico"])
    if _has(text,[r"turism",r"excursion",r"sender",r"trekking",r"caminat",r"aventura",r"guia(?:das|dos|s)?"]):
        if not _has(product+constraints,[r"\b\d+\s*(?:hora|hr|dia|km)",r"duraci[oó]n",r"medio d[ií]a"]):
            add("duracion","Oferta turística","¿Cuánto dura cada experiencia y qué incluye?",
                "Hay actividades turísticas pero no se confirma duración y alcance.", "alta",["productos"])
        if not _has(product+constraints,[r"seguridad",r"protocolo",r"seguro",r"certific",r"emergencia"]):
            add("seguridad","Oferta turística","¿Qué medidas de seguridad y requisitos se informan antes de la excursión?",
                "La información de seguridad no aparece documentada.", "alta",["productos","condiciones"])
        if not _has(product+constraints,[r"lluvia",r"clim",r"cancel",r"reprogram",r"mal tiempo"]):
            add("clima","Oferta turística","¿Qué pasa con la actividad si llueve o hay mal tiempo?",
                "Las políticas climáticas no están confirmadas.", "alta",["condiciones"])
        if not _has(product+constraints,[r"grupo",r"cupos?",r"capacidad",r"m[aá]ximo",r"personas por"]):
            add("cupos","Oferta turística","¿Cuántas personas admite cada salida y qué fechas están disponibles?",
                "La capacidad y disponibilidad requieren confirmación.", "media",["productos","condiciones"])
    if _has(text,[r"restaur",r"cafeter",r"almuerzo",r"comida",r"pasteler",r"cocin",r"buffet"]):
        if not _has(product+constraints,[r"horari",r"lunes",r"martes",r"domingo",r"\b\d{1,2}:\d\d"]):
            add("horarios","Gastronomía","¿Cuáles son los días y horarios reales de atención?",
                "No aparecen horarios concretos.", "alta",["condiciones"])
        if not _has(product+constraints,[r"menu",r"men[uú]",r"carta",r"stock",r"disponib"]):
            add("carta","Gastronomía","¿Existe una carta o menú vigente con disponibilidad confirmada?",
                "Los productos requieren respaldo operativo.", "media",["productos"])
    if _has(text,[r"abogad",r"jur[ií]dic",r"m[eé]dic",r"salud",r"nutrici",r"psicolog"]):
        add("revision_experta","Contenidos sensibles",
            "¿Quién revisará las afirmaciones técnicas y las autorizaciones antes de publicar?",
            "Es importante incluir revisión profesional y evitar afirmaciones no verificadas.",
            "alta",["negocio","productos"])
    strengths=[]
    if answers.get("diferencia"):
        strengths.append({"area":"Diferenciación","fuente":"diferencia",
                          "observacion":"Existe una declaración del cliente sobre por qué lo eligen; requiere contrastarse."})
    if answers.get("publico"):
        strengths.append({"area":"Audiencia","fuente":"publico",
                          "observacion":"Existe una descripción del público actual que puede orientar entrevistas y mensajes."})
    if answers.get("referentes"):
        strengths.append({"area":"Referencias visuales","fuente":"referentes",
                          "observacion":"Existen referencias declaradas para investigar, no para copiar ni adoptar automáticamente."})
    return {
        "engine":"rules_strategic_audit_0_1",
        "status":"pendiente_revision_humana",
        "preguntas_priorizadas":questions,
        "informacion_aprovechable":strengths,
        "num_preguntas":len(questions),
        "apto_para_producir":False,
        "corriente_madre_aprobada":False,
        "limitaciones":"Detección por palabras clave, no interpreta semántica. Una pregunta sugerida puede estar ya respondida implícitamente; siempre comprobar con el cliente."
    }
