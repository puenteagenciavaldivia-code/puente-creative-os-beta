# Creative OS 1.0 — consolidación experimental

10 de noviembre de 2026. Base inicial: `aa39f218549ed9750c87faeb0e9c9d365bb6caee`. Primera rama: `experiment/creative-os-1-dossier`. Continuación: `experiment/creative-os-1-decisions`, basada en `54b38289b56c11014129d8702103c9f25adb6e40`.

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
| P0 | Decisiones durables y autoría verificable | Repositorio local transaccional y demo persistente implementados en la continuación; integración con identidad verificada y disco durable productivo pendiente. Panel Beta conserva guardado en sesión |
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

## Continuación — decisiones persistentes locales

Se añadió `decision_store.py`, con SQLite de la biblioteca estándar: revisiones inmutables por API, decisiones nuevas sin sobrescribir anteriores, comprobación de integridad y aislamiento lógico por agencia/proyecto. Cada decisión queda ligada a versión, hash del dossier y actor proporcionado por el servidor. Una revisión posterior no hereda la aprobación anterior. El actor de auditoría no se obtiene del campo de nombre libre del dossier.

Se reutilizaron `bind_dossier`, `approve_bound`, los modelos de revisión Beta y el patrón transaccional SQLite de laboratorio ya documentado. No se creó otro motor de autorización creativa ni se adaptó Apps Script. Los actores deben llegar desde una futura autenticación real; la política se inyecta exclusivamente desde el servidor, deniega por defecto y se consulta en cada llamada, también en reintentos. Una excepción de política no concede acceso.

Guardar versión o decisión y su evento de auditoría sucede en una transacción `BEGIN IMMEDIATE`. Un fallo al insertar el evento revierte la operación. La versión esperada evita escrituras perdidas; un identificador de solicitud devuelve el mismo resultado si se repite y rechaza reutilización con otro contenido. El historial registra acción, actor, fecha y resultado para mutaciones satisfactorias y denegaciones de política. Los conflictos de versión/validación se devuelven como errores y no generan eventos persistentes; cuando la base falla no se garantiza poder registrar el propio fallo.

`decision_demo.py` permite revisar ese recorrido sin conectar el panel Beta: guardar propuesta, aprobar/rechazar, recuperar en otra sesión y descargar decisión/historial. Hay dos identidades SELECCIONABLES y FICTICIAS: dirección y operación; operación no aprueba. Es un escenario de prueba, no un alta ni una asignación de roles a personas reales. No se modificó el flujo productivo ni se habilitó un login aparente. La base usa `.local/` y queda fuera de Git. No hay migración de datos existentes ni endpoints nuevos.

### Evidencia de la continuación

**102/102 pruebas locales satisfactorias**: 70 anteriores + 28 de almacenamiento + 4 de UI persistente. Python 3.12.14, SQLite 3.53.1, Streamlit 1.67.0. Registro actual en `docs/VALIDACION_LOCAL.txt`.

Pruebas nuevas: recuperación con instancia y proceso Python nuevos; recuperación de decisión tras reiniciar la sesión Streamlit; aislamiento de agencia/proyecto; consulta sin permiso de aprobación; actor desconocido/desactivado; denegación por defecto y ante fallo de política; reintentos idénticos y colisión de identificadores; aprobación obsoleta invalidada; rechazo posterior a aprobación; permisos de producción siempre falsos; rollback ante fallo de auditoría; detección de alteración de revisión, evento o decisión; dos escritores locales simultáneos con un único ganador; copia mediante SQLite backup y restauración local con igualdad de decisión e historial. No se probó una restauración operativa en Google ni hosting.

La compilación y `git diff --check` pasan. No se añadieron dependencias. Las pruebas escriben solo en directorios temporales con fixtures y limpian sus bases. No hubo llamadas a servicios externos, despliegues, cambios de credenciales, ejecuciones GAS ni cierre de etapa.

### Límites y dictamen actualizado

- La persistencia se ha demostrado en disco LOCAL. Streamlit Community Cloud o múltiples réplicas requieren una decisión de almacenamiento durable; no asumir que SQLite local resuelve ese entorno.
- El encadenamiento SHA-256 detecta modificaciones accidentales verificadas en pruebas, pero no es firma, no repudio ni almacenamiento inmutable. Un administrador de la base puede reescribir una cadena completa o truncarla. La copia no está cifrada; retención, permisos del sistema y gestión de respaldos siguen pendientes para datos reales.
- No se probó OIDC ni autenticidad de `issuer/sub`. La API de almacenamiento debe ser interna y nunca aceptar actores/políticas desde JSON cliente. La política de la demo es ficticia. No se probó revocación global ni revocación retroactiva de aprobaciones anteriores.
- Hay transacciones y contención comprobadas dentro de un archivo SQLite local. No hay atomicidad distribuida con Apps Script ni concurrencia entre hosts. La política de acceso está fuera de esa transacción y requiere una fuente autoritativa antes de integración real.
- La evaluación creativa humana, el alcance contractual del PDF y los pilotos reales siguen pendientes. Estos cambios no cierran los otros P0 del registro.

**NO APTO para integrar al núcleo productivo. APTO para revisión local del dossier con historial persistente.** Próxima prioridad: contrato de identidad verificada y persistencia durable para el entorno elegido, con revisión humana de los dossiers en paralelo. No duplicar el repositorio de decisiones si ese contrato puede adaptarse; no desplegar esta demo de identidades seleccionables.

## Continuación — contrato de identidad del servidor

Rama `experiment/creative-os-1-identity`, sobre el contenido de la rama de decisiones (commit remoto `02711868665aa4a187f19674cc21076671851112`).

`identity_boundary.py` prepara un punto interno que requiere token, audiencia configurada en servidor, verificador criptográfico y consumo atómico de nonce de sesión. No acepta un objeto Actor ni roles enviados por el navegador. Comprueba emisor Google, audiencia única, azp si existe, sub, iat/exp finitos y nonce. Devuelve Actor usando sub y emisor canónico; los correos y roles declarados en claims no conceden permisos. El almacén aplica su política por proyecto después, incluso si la identidad se verificó.

El adaptador opcional `google_library_verifier` delega la verificación a `google.oauth2.id_token.verify_oauth2_token`, con audiencia explícita y tiempo límite en el transporte de certificados. No se ejecuta al importar. Su dependencia se declara aparte en `requirements-oidc.txt`; no se cambió la instalación habitual, el panel, credenciales ni configuración de Google. Referencias primarias consultadas: https://google-auth.readthedocs.io/en/latest/reference/google.oauth2.id_token.html y https://developers.google.com/identity/gsi/web/guides/verify-google-id-token .

**Validación: 128/128 pruebas locales aprobadas**, 26 nuevas sobre el contrato de identidad. Verificador y nonce simulados, sin llamadas externas: emisor/audiencia/azp incorrectos; expiración y fechas futuras; números no finitos; sub inválido; nonce ausente, incorrecto o reutilizado; errores del verificador y del almacén de nonce; mensajes sin token/detalles sensibles; identidad válida sin permisos denegada; recorrido de identidad simulada → política → revisión/decisión persistente. Se mantuvieron las 102 pruebas anteriores. Compilación y diff correctos. Registro consolidado en `docs/VALIDACION_LOCAL.txt`.

**Límites:** no se probó firma criptográfica con tokens reales ni se instaló o ejecutó el adaptador opcional de Google; las pruebas verifican el contrato con un verificador ficticio. No hay callback OAuth, gestión de state/PKCE, cookies/sesión, logout, renovación o rate limiting. El consumidor de nonce es un contrato: todavía debe implementarse como almacenamiento de sesión del servidor, con caducidad, consumo atómico y asociación a la sesión; no basta con un set en memoria compartido en producción. El endpoint futuro nunca debe aceptar funciones/verificadores desde el cliente. La dependencia opcional y el acceso a certificados necesitan prueba de integración posterior. No se configura OAuth ni se crean credenciales con esta entrega.

**Dictamen: APTO para revisar el contrato y preparar integración aislada; NO APTO para activar acceso real ni integrar al núcleo.** Próxima prioridad: cerrar plataforma de alojamiento y almacenamiento durable, y después autorizar nominalmente configuración OAuth y ensayo end-to-end. La evaluación creativa humana de los dossiers continúa pendiente y no debe darse por realizada.

**04.01 ABIERTA — SIN LOGIN REAL NI DESPLIEGUES — 04.02 NO INICIADA.**
