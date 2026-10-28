"""Preselección transparente sin modelo: útil si la API todavía no está conectada.

No es inteligencia semántica ni investigación histórica; requiere revisión.
"""
import re
import unicodedata
from design_catalog import read_catalog

# Emparejamientos orientativos de necesidades y lenguaje del briefing.
KEYWORD_WEIGHTS={
    "Art Nouveau":{"naturaleza":3,"botanic":4,"planta":4,"bosque":3,"ornament":2},
    "Arts & Crafts":{"artesan":4,"oficio":4,"hecho a mano":5,"local":2,"patrimonio":3},
    "Estilo Tipográfico Internacional":{"claridad":4,"informacion":4,"seguridad":2,"consulta":2,"servicio":2},
    "Bauhaus":{"funcional":3,"sistema":3,"educa":3,"moderno":2},
    "Diseño vernáculo":{"barrio":3,"regional":2,"valdivia":2,"comunidad":3,"tradicion":3},
    "Diseño editorial contemporáneo":{"fotografia":3,"documental":4,"real":2,"editorial":3,"relato":2},
    "Diseño de información":{"informacion":4,"instruccion":4,"pregunt":3,"guia":2,"explica":3},
    "Minimalismo editorial":{"sobrio":4,"simple":3,"limpio":3,"tranquilo":3,"calma":3},
    "Diseño biofílico aplicado":{"naturaleza":4,"organico":3,"bosque":3,"medioambiente":4,"plantas":3},
    "Constructivismo":{"campaña":3,"impacto":3,"evento":2,"energia":3},
    "Pop Art":{"entretenimiento":3,"divertido":3,"humor":2,"promocion":3},
    "Art Déco":{"elegante":3,"hotel":4,"lujo":4,"premium":3},
    "Grunge editorial":{"rock":3,"underground":4,"musica":2,"alternativo":3},
}
def norm(value):
    if isinstance(value,list):
        value=" ".join(map(str,value))
    v=unicodedata.normalize("NFKD",str(value or "").lower())
    return "".join(c for c in v if not unicodedata.combining(c))

def preselect(answers,count=3):
    if not isinstance(answers,dict):
        raise ValueError("Respuestas no válidas.")
    fields=("negocio","personalidad","diferencia","destacar","publico","referentes","evitar","objetivo","tono")
    text=" ".join(norm(answers.get(x)) for x in fields)
    if len(text.strip())<30:
        return []
    candidates=[x for x in read_catalog() if x["categoria"] in ("histórica","enfoque")]
    scored=[]
    for entry in candidates:
        weights=KEYWORD_WEIGHTS.get(entry["nombre"],{})
        score=sum(weight for word,weight in weights.items() if word in text)
        if score>0:
            scored.append((score,entry))
    scored.sort(key=lambda item:(-item[0],item[1]["id"]))
    distinct=[]
    seen=set()
    for score,entry in scored:
        # Avoid three very similar options.
        family=("organico" if entry["nombre"] in ("Art Nouveau","Diseño biofílico aplicado")
                else "editorial" if entry["nombre"] in ("Minimalismo editorial","Diseño editorial contemporáneo")
                else entry["nombre"])
        if family in seen:
            continue
        distinct.append((score,entry))
        seen.add(family)
        if len(distinct)==count:break
    if len(distinct)<count:
        for entry in candidates:
            if entry["id"] not in {x[1]["id"] for x in distinct}:
                distinct.append((0,entry))
            if len(distinct)==count:break
    result=[]
    original=[(k,str(answers[k])) for k in fields if answers.get(k)]
    evidence="; ".join(k+": "+value[:100] for k,value in original[:2])
    for score,entry in distinct:
        result.append({
            "nombre":entry["nombre"],
            "fundamento":"Hipótesis preliminar basada en palabras presentes en el briefing ("+evidence+"). Coincidencia léxica, requiere análisis del director creativo.",
            "diferenciacion":"Explorar "+", ".join(entry["rasgos"])+
                " y contrastarlo con otras propuestas, objetivos y referencias de la competencia.",
            "riesgos":"Revisar: "+", ".join(entry["riesgos"])+
                ". La pertinencia real no está evaluada semánticamente.",
            "catalogo_id":entry["id"],"tipo":"preseleccion_por_reglas",
            "puntaje_lexico":score
        })
    return result
