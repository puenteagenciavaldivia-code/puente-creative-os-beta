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

## Continuación — ensayo criptográfico preparado, bloqueado por dependencia

Rama `experiment/creative-os-1-token-verification`, sobre el contenido del contrato de identidad (`0752bab2923a175e5215abb334a49ba609ca38d0`). Se añadió una suite opcional de nueve pruebas con RSA y certificados efímeros ficticios: firma correcta, clave incorrecta, payload alterado, token sin firma, audiencia/emisor incorrectos, expiración, repetición de nonce y fallo de certificados. El transporte de certificados se sustituye por un fixture y cualquier uso del transporte HTTP real queda bloqueado dentro de esos tests. No se registra material privado.

No se modificó el adaptador, el login, la UI ni la configuración de Google. No se cambiaron credenciales ni se desplegó. `requirements-test-oidc.txt` declara dependencias opcionales; no se cambió el workflow para instalarlas automáticamente.

**Estado comprobado:** google.auth no está instalado, cryptography ya está disponible. La instalación de dependencias fue rechazada por revisión automática, que citó una restricción anterior de trabajo de solo lectura. No se eludió ni reintentó. El siguiente paso requiere aprobación expresa de instalación LOCAL, sin nuevas cuentas ni permisos Google.

**Resultado actual: 137 tests descubiertos, 128 aprobados y 9 OMITIDOS.** No informar 137/137 aprobados. Compilación y diff satisfactorios. Los nueve tests nuevos aún requieren ejecución y, si corresponde, correcciones; su código está preparado para revisión, no validado criptográficamente. El registro de esta tanda está en `docs/VALIDACION_LOCAL.txt`.

Próxima acción preparada, pendiente de autorización: instalar `requirements-test-oidc.txt` en el entorno aislado y ejecutar exclusivamente la suite criptográfica; después repetir regresión solo si se corrige código. Aun con firmas locales aprobadas, seguirán pendientes confianza en certificados Google reales, configuración OAuth, gestión de sesión y prueba real de inicio de sesión.

**DICTAMEN: BLOQUEADO para completar la validación criptográfica; NO APTO para integrar al núcleo. 04.01 ABIERTA; 04.02 NO INICIADA.**

### Resolución del bloqueo — instalación expresamente autorizada

El usuario autorizó instalar dependencias únicamente en el entorno aislado. Se instaló `requirements-test-oidc.txt`: google-auth 2.62.1, cryptography 49.0.0, requests 2.34.2. No se crearon credenciales, no se cambió Google ni el sistema productivo.

Se ejecutó `python3 -m unittest discover -s tests -p test_google_token_crypto.py -v`: **9/9 APROBADAS, 0 omitidas**, en 0,242 segundos. El adaptador utiliza ahora en estas pruebas la biblioteca oficial y firmas RSA reales sobre tokens ficticios, con certificado efímero local. El transporte de certificados se sustituye por un fixture y el transporte HTTP real está bloqueado durante la prueba.

Resultado: firma válida aceptada; clave incorrecta, payload modificado, token sin firma, audiencia incorrecta, emisor incorrecto, expiración, nonce repetido y fallo al obtener certificados rechazados. No se modificó código funcional. No se repitieron los otros 128 tests: su resultado previo se conserva, y las nueve omisiones anteriores quedaron resueltas por esta ejecución específica. No se afirma una nueva ejecución conjunta de 137 tests. Evidencia adicional en `docs/VALIDACION_CRIPTO_LOCAL.txt`.

**Dictamen actualizado: APTO para revisión del adaptador criptográfico offline; NO APTO para integrar al núcleo productivo.** Sigue pendiente verificar certificados de Google reales, configurar el flujo OAuth aprobado, implementar sesión/state/PKCE y consumidor durable de nonce, y escoger almacenamiento durable para el entorno de alojamiento. Ninguna prueba utiliza cuentas reales ni valida ese flujo end-to-end.

**04.01 ABIERTA — BLOQUEO LOCAL DE DEPENDENCIAS RESUELTO — SIN DESPLIEGUES — 04.02 NO INICIADA.**

## Tanda de preparación del piloto — sesión, contrato y recuperación

Rama `experiment/creative-os-1-pilot-readiness`, continuación del contenido de `5a5a84e5054fd898e37d26622e0cb80277266013`.

### Implementación

- `session_store.py`: desafíos de acceso con caducidad, state de un solo uso y binding de navegador; consumo atómico en SQLite antes de verificar identidad; errores de verificación consumen el desafío. Sesiones opacas, handles/state almacenados como SHA-256, expiración absoluta/inactividad, revocación individual y de todas las sesiones locales de un actor. No usa roles de claims para conceder acceso.
- `client_delivery.py`: proyección de entrega por contrato del servidor y proyecto. Exige aprobación creativa vigente, permite únicamente entregables conocidos y exporta solo la ruta seleccionada. Excluye revisión interna, auditoría, datos del actor, riesgos internos y alternativas no seleccionadas. La comparación exige un resumen separado para cliente, no reutiliza el razonamiento interno. Las fuentes requieren tipo público/licenciado y marca explícita de aprobación para cliente; esa marca no acredita por sí sola una licencia real. HTML escapado y etiquetas en español. El PDF interno previo no se transforma automáticamente en documento externo.
- `store_backup.py`: copia consistente con SQLite backup, integrity_check, manifiesto SHA-256, creación exclusiva sin sobrescritura y restauración en base nueva. La restauración conserva decisiones/historial, pero invalida sesiones y desafíos de login anteriores: evita reactivar accesos revocados después de la copia. No implementa respaldos cloud ni cifrado.
- `pilot_rehearsal.py`: ensayo local completo con fixture de identidad → sesión → política por proyecto → versión → decisión → entrega contractual → copia/restauración → cierre de sesión. La identidad se SIMULA, no se presenta como inicio de sesión Google ni aceptación humana. Borra el directorio temporal al terminar. Evidencia exportada sin handles ni tokens en `examples/pilot_rehearsal.json`; ejemplo externo ficticio en `examples/client_delivery_synthetic.html`.

### Verificación final

**170/170 tests locales aprobados, cero omitidos**: 137 previos, incluidas nueve firmas criptográficas offline, más 33 de esta tanda. Casos nuevos: recuperación de sesión tras reinicio, caducidad y logout, callback duplicado y dos callbacks locales simultáneos con un solo ganador, vinculación a navegador, fallo de verificador, handles no almacenados en claro, invalidación de sesiones al restaurar; contrato ajeno/desconocido, aprobación ausente/obsoleta, exclusión de campos internos, proyección independiente del original, HTML escapado; copia y restauración sin sobrescritura, detección de alteración, original intacto y ensayo integrado.

Comandos: `python -m unittest discover -s tests -v`, `python -m compileall -q .`, `git diff --check`. Resultado consolidado en `docs/VALIDACION_LOCAL.txt`. El ensayo reporta versión 1, dos eventos históricos, decisión persistida, producción false, secciones strategy/direction y restauración coincidente. El dashboard nuevo no se desplegó ni se conectó a estos servicios.

### Límites y criterios pendientes

Estos módulos son APIs internas: la aplicación deberá proporcionar contrato, política, binding y verificador desde el servidor. No aceptar esos parámetros como autoridad del cliente. No hay rutas OAuth, PKCE, cookies Secure/HttpOnly/SameSite, protección CSRF completa, rate limiting, configuración del proveedor ni verificación real de la cuenta. No se autoriza desplegar las demos con selectores de identidad.

La expiración y revocación comprobadas afectan a esta base LOCAL; no son logout global Google ni revocación entre servidores. Los callbacks concurrentes se probaron sobre un archivo local. Hace falta implementar retención/limpieza de desafíos caducados y controlar cuota de intentos antes de exponer el acceso. Las bases y backups pueden contener datos sensibles y no están cifrados. El manifiesto es integridad, no firma ni prueba contra un administrador malicioso. No publicar ni versionar bases/certificados privados.

La selección de hosting y almacenamiento durable continúa abierta: SQLite requiere un host con disco persistente y un escritor coordinado. No se certifica que el alojamiento Streamlit existente garantice esa condición ni costo cero. Mantener frontend Streamlit y adaptar este contrato a un backend durable evita reconstruir la dirección creativa; ningún proveedor nuevo quedó contratado/configurado.

La evaluación humana de los tres dossiers, la confirmación de contratos reales y la licencia de fuentes siguen pendientes. No son sustituibles por más tests de código. También falta conectar la proyección contractual al panel con datos autorizados; no se modificó la salida habitual de clientes ni el backend productivo.

**Dictamen: APTO para ensayo local integrado y revisión; NO APTO para núcleo productivo.** Próximo hito: decisión concreta de alojamiento/disco durable y revisión creativa de tres dossiers, antes de autorizar configuración OAuth y un piloto humano. No ampliar a más infraestructura ni repetir pruebas sin un cambio que lo justifique.

**04.01 ABIERTA — 170 PRUEBAS LOCALES — SIN MAIN/PRODUCCIÓN — 04.02 NO INICIADA.**
