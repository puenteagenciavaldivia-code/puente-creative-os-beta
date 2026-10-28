# PUENTE Creative OS — Método de dirección creativa basado en fuentes

**Estado:** investigación metodológica inicial; no estudio completo de los libros ni certificación histórica de las 41 referencias del catálogo.

## 1. Fuentes editoriales consultadas (descripción e índices)

Estas son referencias verificadas mediante sus editoriales o fichas bibliográficas públicas; **no se afirma haber leído sus textos completos**.

1. **Philip B. Meggs y Alston W. Purvis**, *Meggs' History of Graphic Design*, sexta edición, Wiley, 2016. El índice distingue Arts & Crafts, Art Nouveau, Bauhaus y nueva tipografía, Estilo Tipográfico Internacional, identidad corporativa y posmodernismo. Función en Creative OS: *clasificación y contexto histórico*, no recetas de diseño. https://www.wiley.com/en-us/meggs%27-history-of-graphic-design-6th-edition-p-9781119136231
2. **Ellen Lupton**, *Thinking with Type*, tercera edición, Princeton Architectural Press, 2024. La autora describe temas de familias tipográficas, tracking, kerning, retículas, alineación y percepción Gestalt. Función: *legibilidad, tipografía y jerarquía*. https://ellenlupton.com/Thinking-with-Type
3. **Timothy Samara**, *Making and Breaking the Grid*, tercera edición, 2023. La ficha publicada en People's Graphic Design Archive recoge su estructura: retícula, tipos y principios, aplicaciones y enfoques no estructurados. Función: *componer sistemas con estructura y saber cuándo romperla*. https://assets.peoplesgdarchive.org/item/18714/making-and-breaking-the-grid
4. **Josef Müller-Brockmann**, *Grid Systems in Graphic Design*, Niggli, 1981. El editor presenta retículas funcionales y aplicaciones consistentes desde piezas pequeñas hasta entornos. Función: *construcción modular*. https://niggli.ch/en/products/rastersysteme-fur-die-visuelle-gestaltung
5. **Wucius Wong**, *Principles of Form and Design*, Wiley, 1993. Su índice incorpora repetición, estructura, similitud, gradación, radiación, anomalía, contraste, textura y espacio. Función: *gramática formal*, no movimiento histórico. https://www.wiley.com/en-us/principles-of-form-and-design-p-9780471285526
6. **Alina Wheeler y Rob Meyerson**, *Designing Brand Identity*, sexta edición, Wiley, 2024. El índice diferencia investigación, estrategia, identidad, puntos de contacto y gestión de activos. Función: *relacionar investigación con alcance contractual, validación y entregables*. https://www.wiley.com/en-us/designing-brand-identity-a-comprehensive-guide-to-the-world-of-brands-and-branding-6th-edition-p-9781119984818
7. **Michael Bierut**, *How to Use Graphic Design to Sell Things, Explain Things, Make Things Look Better…*, edición revisada, Thames & Hudson, 2021. Monografía de casos de proyectos y decisiones para clientes. Función: *criterio contextual y aplicado*. https://www.thamesandhudson.com/products/how-to-use-graphic-design-to-sell-things-explain-things-make-things-look-better-make-people-laugh-make-people-cry-and-every-once-in-a-while-change-the-world

## 2. Taxonomía

- **Movimiento histórico / tradición:** un conjunto reconocible con contexto, actores y principios (por ejemplo Bauhaus, Art Nouveau, Internacional Tipográfico).
- **Enfoque sistemático:** forma de organizar la comunicación, sin pretender que sea un movimiento histórico cerrado (diseño de información, minimalismo editorial).
- **Técnica:** proceso productivo (risografía, collage, grabado).
- **Lenguaje fotográfico:** una manera de construir imágenes (documental, editorial).
- **Recurso:** componente secundario (pictogramas, mapas, tipografía expresiva).
- **Tendencia:** corriente temporal o revival de lenguajes (Y2K, brutalismo digital).

No elevar técnicas, fotografías o tendencias a movimientos históricos. Una dirección madre puede ser una tradición histórica o un enfoque coherente; los otros lenguajes funcionan como elementos secundarios según criterio del diseñador.

## 3. Matriz de evaluación editorial

Evaluar cada dirección por: posición competitiva, adecuación de público, cumplimiento del objetivo, rigor histórico-contextual, viabilidad de producción, accesibilidad de lectura, diferenciación respecto al portafolio y coherencia del sistema visual.

**La justificación no se reduce a coincidencias de palabras:** «bosque» no implica que Art Nouveau sea la mejor opción; «premium» no implica Art Déco. La propuesta se contrasta con competencia, presupuesto, fotografías disponibles, público y objetivo.

El diseño debe explicar:
- Cómo resuelve jerarquía, tipografía, composición e imagen.
- Qué elementos de la marca existente conserva.
- Cómo funcionaría en un carrusel, una historia, un reel y una pieza impresa si fueran parte del contrato.
- Qué riesgos existen (legibilidad, saturación, cliché cultural, dificultad de producción, falsos claims).
- Qué datos sustentan la hipótesis y cuáles siguen pendientes.
- Qué alternativa distinta ofrece respecto a las otras dos.

## 4. Implementación real y límites

`design_catalog.json`: vocabulario curado inicial con 41 entradas; no es una base histórica exhaustiva. `design_methodology.py`: criterios y fuentes. `ai_art_direction.py`: llamada opcional a IA con tres hipótesis estructuradas, referencias al catálogo y comprobación de citas literales del briefing. `creative_preselection.py`: alternativa basada en palabras, **no IA**, disponible sin API.

**No hay recomendación generativa automática en el despliegue sin `OPENAI_API_KEY` y autorización de transferencia del briefing.** El cliente nunca recibe sugerencias del panel; solo el director de arte puede evaluar las propuestas.

El motor generativo no tiene acceso directo al texto completo de los libros; sus criterios se derivan de las páginas editoriales e índices públicos revisados y del catálogo curado. Un siguiente proyecto de investigación podría incorporar notas originales y fuentes autorizadas, con licencia y trazabilidad para cada corriente.

## 5. Auditoría de calidad posterior

Solicitar comparaciones entre tres alternativas, explicar por qué **no** utilizar dos de ellas, revisar condiciones de producción y evitar repetición entre marcas. Guardar responsable y decisión final con el briefing, sin usar puntajes automáticos para aprobar.
