"""PUENTE Creative OS Beta 0.5: evaluación heurística, no IA generativa.

Puntuación orientativa de calidad/claridad de respuestas; no una validación de
verdad, estrategia o diseño. Requiere revisión humana.
"""
import re
import unicodedata

WEIGHTS = {
    "identidad": 15,
    "propuesta_de_valor": 20,
    "audiencia": 15,
    "objetivos": 20,
    "visual": 15,
    "diferenciacion": 10,
    "operacion": 5,
}
DIMENSIONS = {
    "identidad": ["nombre", "negocio", "personalidad", "recuerdo"],
    "propuesta_de_valor": ["productos", "diferencia", "destacar"],
    "audiencia": ["publico", "publico_nuevo", "dudas", "tono"],
    "objetivos": ["objetivo", "canales"],
    "visual": ["identidad_visual", "elementos", "referentes"],
    "diferenciacion": ["competencia", "evitar"],
    "operacion": ["materiales", "condiciones"],
}
LABELS = {
    "nombre": "Nombre", "negocio": "Actividad del negocio",
    "personalidad": "Personalidad", "recuerdo": "Recuerdo de marca",
    "productos": "Productos o servicios", "diferencia": "Propuesta de valor",
    "destacar": "Aspecto a destacar", "competencia": "Competidores o referentes",
    "publico": "Público actual", "publico_nuevo": "Público deseado",
    "dudas": "Dudas del cliente", "tono": "Tono",
    "identidad_visual": "Identidad visual", "elementos": "Elementos a conservar",
    "referentes": "Referencias visuales", "evitar": "Elementos a evitar",
    "objetivo": "Objetivo", "canales": "Canales",
    "materiales": "Materiales disponibles", "condiciones": "Condiciones y fechas",
}
# Los desplegables tienen menos exigencia de extensión.
SELECT_FIELDS = {"tono", "identidad_visual", "objetivo", "canales"}
CRITICAL = ("negocio", "productos", "diferencia", "publico", "objetivo")
REQUIRED = {"nombre","negocio","productos","diferencia","publico","identidad_visual","objetivo","canales"}
FOLLOWUPS = {
    "negocio": "¿Qué hace exactamente la marca y en qué contexto ofrece su servicio?",
    "productos": "¿Cuáles son los servicios o productos principales y cómo se entregan?",
    "diferencia": "¿Qué hecho concreto hace que un cliente elija esta marca frente a otra?",
    "publico": "¿Quién compra actualmente? Describe hábitos, necesidades o situaciones concretas.",
    "publico_nuevo": "¿Qué nuevo segmento quieres atraer y por qué?",
    "dudas": "¿Qué preguntas u objeciones frecuentes reciben antes de comprar?",
    "personalidad": "¿Qué tres rasgos de personalidad debe transmitir la marca?",
    "recuerdo": "¿Qué idea quieres que el público recuerde después de conocer la marca?",
    "destacar": "¿Qué beneficio, experiencia o fortaleza deberíamos mostrar primero?",
    "competencia": "¿Qué referentes o competidores observas y qué te gusta o incomoda de ellos?",
    "elementos": "¿Qué elementos gráficos actuales deben respetarse y cuáles pueden cambiar?",
    "referentes": "¿Qué referencias visuales prefieres y qué aspectos específicos te atraen?",
    "evitar": "¿Qué recursos o estilos gráficos deberíamos evitar?",
    "materiales": "¿Qué fotos, logotipos o documentos tienes disponibles y puedes autorizar?",
    "condiciones": "¿Existen fechas, restricciones de producción o aprobaciones que debamos contemplar?",
    "objetivo": "¿Qué acción concreta debería realizar el público y cómo sabremos si funcionó?",
    "canales": "¿En qué canales quieres publicar primero?",
    "nombre": "¿Cuál es el nombre que debe aparecer en las piezas?",
    "tono": "¿Qué tono debería emplear la marca en sus comunicaciones?",
    "identidad_visual": "¿Existe un manual o archivos originales del logotipo?",
}
GENERIC = {
    "buena calidad", "somos los mejores", "todo el mundo",
    "somos diferentes", "crecer", "muchos clientes",
    "todos", "no se", "nose", "ninguno", "nada",
    "etc", "varios", "algo", "normal", "lo mejor",
}
PLACEHOLDERS = {"test", "testing", "prueba", "asdf", "qwerty", "1234",
                "sin informacion", "por definir", "no aplica", "n a", "pendiente"}

def normalize(value):
    if isinstance(value, list):
        value = ", ".join(map(str, value))
    text = str(value or "").lower().strip()
    text = unicodedata.normalize("NFKD", text)
    return "".join(ch for ch in text if not unicodedata.combining(ch))

def field_quality(field, value):
    """Devuelve nivel 0..1 y motivo; no usa inteligencia semántica."""
    if value is None or value == [] or not str(value).strip():
        return 0.0, "Sin respuesta"
    raw = normalize(value)
    if raw == "selecciona una opcion":
        return 0.0, "No se seleccionó una respuesta"
    if field in SELECT_FIELDS:
        if raw in ("aun no lo se", "no lo se"):
            return 0.4, "Respuesta pendiente de definición"
        return 1.0, ""
    cleaned = re.sub(r"[^a-z0-9ñ ]", " ", raw)
    words = cleaned.split()
    letters = re.sub(r"[^a-zñ]", "", cleaned)
    if (raw in GENERIC or raw in PLACEHOLDERS
            or re.fullmatch(r"([a-z]{1,5}|[0-9])\1{2,}", letters or "") 
            or re.search(r"(asdf|qwer|sdfg|dfgh|fghj|hjkl)", letters)):
        return 0.0, "Texto de prueba o demasiado genérico"
    if field == "nombre":
        if len(letters) < 3 or not re.search(r"[aeiou]", letters):
            return 0.0, "Nombre no verificable"
        return 1.0, ""
    # Secuencias de consonantes inusuales: señal débil de texto artificial.
    if len(letters) >= 8 and (not re.search(r"[aeiou]", letters)
                              or re.search(r"[^aeiouñ]{7,}", letters)):
        return 0.0, "Posible texto sin significado"
    if len(words) == 1:
        return (0.35, "Respuesta demasiado breve")
    if len(words) < 5:
        return (0.5, "Falta información concreta")
    if len(words) < 11:
        return (0.75, "Podría incluir más detalles")
    return 1.0, ""

def diagnose(answers):
    fields = {}
    flags = []
    followups = []
    for field in LABELS:
        q, reason = field_quality(field, answers.get(field))
        fields[field] = q
        if q < 0.75 and (field in REQUIRED or bool(answers.get(field))):
            flags.append({"field": field, "issue": reason,
                          "severity": "alta" if field in CRITICAL else "media"})
            followups.append({"field": field, "question": FOLLOWUPS[field]})
    dim_scores = {}
    total = 0.0
    for dim, keys in DIMENSIONS.items():
        assessed = [k for k in keys if k in REQUIRED or bool(answers.get(k))]
        value = round(5 * sum(fields[k] for k in assessed) / len(assessed), 2) if assessed else 0.0
        dim_scores[dim] = value
        total += value * WEIGHTS[dim] / 5
    # Un briefing no puede aparecer listo cuando falla el núcleo de negocio.
    weak_critical = [x for x in CRITICAL if fields[x] < 0.75]
    if weak_critical:
        total = min(total, 59.0)
    elif sum(1 for q in fields.values() if q < 0.75) >= 5:
        total = min(total, 69.0)
    score = round(total, 1)
    if weak_critical or score < 60:
        status = "insuficiente"
    elif score < 80 or flags:
        status = "requiere_aclaracion"
    else:
        status = "apto_para_revision"
    optional_fields = set(LABELS) - REQUIRED
    optional_answered = sum(bool(answers.get(k)) for k in optional_fields)
    # Nunca aprobar automáticamente: corresponde a criterio editorial humano.
    return {
        "score": score,
        "dimension_scores": dim_scores,
        "field_quality": fields,
        "optional_answered": optional_answered,
        "optional_total": len(optional_fields),
        "flags": flags,
        "follow_up_questions": followups[:8],
        "status": status,
        "human_review_required": True,
        "approved": False,
        "engine": "heuristic_beta_0_5",
        "limitations": "Puntaje orientativo de campos informados; omite campos opcionales vacíos de la media. No verifica veracidad, coherencia semántica ni estrategia.",
    }
