"""Método Puente: criterios de evaluación de hipótesis de dirección de arte.

Las categorías históricas proceden de una biblioteca curada. No equiparar
movimiento histórico con técnica, recurso, tendencia o lenguaje fotográfico.
"""
from design_catalog import read_catalog

CRITERIA = {
  "posicionamiento": "¿Aporta diferenciación defendible frente al contexto competitivo?",
  "audiencia": "¿Se comprende y resulta adecuado para el público declarado?",
  "comunicacion": "¿Sirve al objetivo y a los formatos de contenido contratados?",
  "historia_contexto": "¿Usa con propiedad la tradición o movimiento y respeta su contexto?",
  "viabilidad": "¿Se puede producir con archivos, presupuesto, tiempo y capacidades existentes?",
  "accesibilidad": "¿La jerarquía y legibilidad sirven a la información importante?",
  "originalidad": "¿Evita reutilizar una solución previa solo por costumbre?",
  "coherencia": "¿El sistema integra composición, tipografía, imagen y elementos secundarios?",
}
BIBLIOGRAPHY = [
    {"autor":"Philip B. Meggs y Alston W. Purvis","titulo":"Meggs' History of Graphic Design",
     "edicion":"6.ª edición, Wiley, 2016",
     "uso":"Cronología, historia del diseño, movimientos y contexto cultural.",
     "url":"https://www.wiley.com/en-us/meggs%27-history-of-graphic-design-6th-edition-p-9781119136231",
     "alcance":"Ficha del editor e índice verificados; no se consultó el texto completo."},
    {"autor":"Ellen Lupton","titulo":"Thinking with Type",
     "edicion":"3.ª edición, Princeton Architectural Press, 2024",
     "uso":"Legibilidad, composición tipográfica, retícula y jerarquía.",
     "url":"https://ellenlupton.com/Thinking-with-Type",
     "alcance":"Descripción e índice temático públicos de la autora; no se consultó el texto completo."},
    {"autor":"Timothy Samara","titulo":"Making and Breaking the Grid",
     "edicion":"3.ª edición, 2023",
     "uso":"Retículas, desviaciones de estructura y su aplicación.",
     "url":"https://assets.peoplesgdarchive.org/item/18714/making-and-breaking-the-grid",
     "alcance":"Descripción de la obra provista por el autor y el archivo; no se consultó el texto completo."},
    {"autor":"Michael Bierut","titulo":"How to Use Graphic Design to Sell Things, Explain Things, Make Things Look Better...",
     "edicion":"Edición ampliada, Thames & Hudson, 2021",
     "uso":"Proceso de proyecto y criterios de comunicación vinculados a clientes reales.",
     "url":"https://www.thamesandhudson.com/products/how-to-use-graphic-design-to-sell-things-explain-things-make-things-look-better-make-people-laugh-make-people-cry-and-every-once-in-a-while-change-the-world",
     "alcance":"Descripción editorial de casos de estudio; no se consultó el texto completo."},
]

def historical_movements():
    return [x for x in read_catalog() if x.get("categoria")=="histórica"]

def criteria_text():
    return "\n".join(key+": "+value for key,value in CRITERIA.items())
