# Creative OS 1.0 — consolidación experimental

10 de noviembre de 2026. Base: `aa39f218549ed9750c87faeb0e9c9d365bb6caee`. Rama: `experiment/creative-os-1-dossier`.

## Resultado de producto

Un dossier de dirección creativa puede prepararse, compararse, revisarse y entregarse sin generar una gráfica. Se reutiliza el motor del laboratorio DCP-02, con adaptador al briefing y la revisión Beta. La producción manual, híbrida o IA permanece opcional y requiere una autorización separada. No se añadió un editor de diseño, publicación automática ni llamadas a IA.

La rama incorpora:

- `dossier_engine.py`: validación DCP-02 robustecida y exportación HTML; contenido no válido no se aprueba ni exporta.
- `dossier_adapter.py`: importación JSON con límites, bloqueo de claves duplicadas y números no finitos, correspondencia de marca e integridad del briefing/auditoría; compatibilidad con la revisión Beta sin modificarla. La aprobación exige citas exactas del briefing en cada alternativa y resolución de preguntas pendientes.
- `dossier_ui.py`: importación, comparación, evidencia, previsualización, descarga HTML/PDF, decisión humana y traspaso opcional. Nueva pestaña Dossier en el panel Beta; no introduce llamadas al backend.
- `dossier_demo.py`: recorrido autónomo con tres marcas ficticias, sin configuración, secretos, Google ni datos de clientes.
- `dossier_pdf.py`: PDF editorial descargable con alternativas, criterios, restricciones, aplicaciones, fuentes y límites.
- Correcciones concretas en Beta: producción exige un booleano verdadero; el encargo rechaza una pieza cuyo contenido cambió conservando su ID.
- CI instala las dependencias declaradas antes de importar módulos; el workflow anterior no las instalaba. No se cambió la configuración de credenciales, permisos o despliegue.

## Reutilización y alternativas

Se eligió adaptar DCP-02 + Streamlit frente a construir otra aplicación o un motor de propuestas paralelo. Es compatible con los objetos `record`, `audit`, `review` y las salidas de `graphic_production.py`, reduce duplicación y mantiene el método de investigación manual con ChatGPT. El adaptador hace copias y nunca convierte una aprobación creativa en permiso de producción.

Procedencia: paquete `PUENTE_CREATIVE_OS_DCP_02_LAB.zip`, resumen ejecutivo versión 3 recuperado el 10/11/2026. Se reutilizaron motor y contrato; no se publicaron el ejemplo de una clienta ni sus materiales. Los tres fixtures públicos de esta rama se redactaron desde cero con marcas ficticias. No constituyen pilotos con usuarios.

## Validación ejecutada

Entorno local: Python 3.12; Streamlit 1.67.0, instalación dentro del intervalo declarado. No se verificó cada versión del intervalo >=1.40,<2 ni Python 3.11 en este entorno. El código evita APIs nuevas exclusivas de 1.67 en la capa de dossier; `components.html` funciona pero emite advertencia de deprecación en la versión instalada.

- Base, después de instalar dependencias: 29 pruebas existentes satisfactorias. Sin instalar dependencias, la importación fallaba por `requests` ausente; esa evidencia motivó la corrección del workflow.
- Resultado final: **70/70 pruebas satisfactorias** con `python3 -m unittest discover -s tests -v`.
- Incluye 34 pruebas de integración, 3 de PDF/encargo y 4 recorridos Streamlit AppTest: tres casos, JSON inválido, decisión creativa y edición que invalida aprobación. Los 29 tests Beta se mantienen.
- `python3 -m compileall -q .` y `git diff --check`: satisfactorios.
- Tres dossiers PDF A4 generados; cuatro páginas por caso. Se renderizaron los tres; se corrigió una página huérfana de riesgos en Nodo Semilla y se revisó la versión corregida. HTML imprimible también disponible.
- Intento de captura del navegador local bloqueado por `socket() failed: Operation not permitted` en Chromium. AppTest sí ejecutó interacción y validación. No se afirma una inspección visual completa del dashboard en navegador ni una prueba del hosting Streamlit.
- No se llamaron endpoints Google/Beta, no se ejecutaron GAS-AUTH01/GAS-AUDIT01 ni se utilizaron cuentas o claves reales. No se desplegó ni fusionó a main.

Las pruebas comprueban contrato y controles, no superioridad creativa, eficacia publicitaria o aceptación humana. Las citas exactas solo prueban correspondencia con texto aportado; no veracidad externa. `visual_signature` detecta coincidencia declarada, no similitud visual semántica.

## Plan de ocho semanas y estado de áreas

Se recuperó de continuidad el esquema de ocho hitos: S1 alcance/arquitectura; S2 inteligencia creativa; S3 dossier; S4 flujo integrado en rama; S5 seguridad; S6 tres pilotos; S7 candidata; S8 aceptación/respaldo/lanzamiento interno. No se recuperó la lista literal de seis condiciones de aceptación mencionada en el chat original: no se reconstruye como aprobación previa.

| Área / hito | Estado verificable | Pendiente para cierre |
|---|---|---|
| S1 alcance | Dirección Creativa Primero acotada; stack actual conservado | Dirección ratifica criterios finales y alcance contractual |
| Briefing, auditoría y aclaraciones | Implementación Beta existente; regresión local aprobada | Flujo real con acceso individual y almacenamiento seguro |
| S2 inteligencia creativa | Citas, alternativas, diferenciación y límites verificables | Evaluación humana de criterio; investigación externa verificable |
| S3 dossier | HTML/PDF y comparación utilizables con fixtures | Revisión humana visual/editorial y exclusión por contrato del documento externo |
| S4 flujo | Integración de código y AppTest en rama | Validación del panel completo sin backend productivo; prueba en entorno autorizado |
| S5 seguridad/confiabilidad | Importación, integridad y permisos de producción reforzados | OIDC real, roles por proyecto, persistencia y auditoría de decisiones, respaldo/restauración |
| S6 pilotos | Tres casos sintéticos disponibles | Tres pilotos humanos controlados; no equivalen a los fixtures |
| Producción y QA | Traspasos manual/híbrido/IA separados; cero generación automática | Validación de activos, licencias, piezas y aprobación humana final |
| S7 candidata | Módulo candidato en revisión | Corregir resultados de pilotos y bloqueos de seguridad |
| S8 aceptación | No alcanzada | Condiciones de cierre, respaldo y reversión verificados; autorización de integración |

## Registro único de pendientes de esta rama

| Prioridad | Pendiente | Evidencia / condición de salida |
|---|---|---|
| P0 | Acceso individual y permisos por proyecto | Panel actual usa contraseña compartida; no se tocó. OIDC sigue sin integración real |
| P0 | Decisiones durables y autoría verificable | La nueva UI guarda solo en sesión y exporta JSON; nombres/hashes no autentican a una persona |
| P0 | Revisar salida externa y alcance de contrato | PDF es exploratorio interno; no se implementó aún filtrado automático por contrato |
| P1 | Revisión creativa humana de tres casos | No hay aprobación ni medición de utilidad de usuarios reales |
| P1 | Validación visual de dashboard y panel completo | AppTest aprobado; Chromium local bloqueado; hosting no probado |
| P1 | Compatibilidad de versiones | Probar mínimo de Streamlit/Python declarado o acotar versiones mediante decisión posterior |
| P1 | Referencias y derechos | Los fixtures usan fuentes internas sintéticas, no investigación de mercado ni licencias verificadas |
| P2 | Sustituir API de HTML deprecada | Mantener sandbox y compatibilidad; no cambiar por una inserción HTML insegura |
| P2 | GAS-AUDIT01 real | Preparación previa local 13/13; no se ejecutó de nuevo ni se dio por validada persistencia Google |

## Dictamen y próxima prioridad

**NO APTO para integrar al núcleo productivo. APTO para revisión técnica y creativa aislada de la rama.** El módulo ya produce entregables utilizables con datos ficticios; el producto completo no está terminado ni certificado. El siguiente avance debe ser una revisión humana de los tres dossiers y un entorno de integración con acceso individual y persistencia de decisiones, cerrando P0 sin reconstruir este módulo.

Reversión: abandonar la rama restaura la base main; no hubo migraciones ni escrituras de datos. Antes de integrar, revisar el diff y repetir solo los checks afectados por nuevas modificaciones. No usar datos de clientes hasta cerrar acceso, privacidad y autorización. Ningún estado de esta entrega cierra 04.01 ni inicia 04.02.

**04.01 ABIERTA — RAMA EXPERIMENTAL PARA REVISIÓN — SIN DESPLIEGUE — 04.02 NO INICIADA.**
