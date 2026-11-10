# PUENTE 04.01 — preparación de la prueba real 01

Fecha: 2026-11-10. Estado: ENTRADA IMPLEMENTADA Y PROBADA LOCALMENTE; ejecución real NO INICIADA.
Complementa el registro único `CREATIVE_OS_1_REVISION.md`; no reemplaza evidencias anteriores.

## Decisión técnica propuesta

Primer piloto en un único equipo controlado por Puente, con disco local persistente y
dos operadores en turnos separados. Streamlit escucha exclusivamente en loopback;
retorno propuesto `http://localhost:8501/oauth2callback`. Google OIDC nativo de
Streamlit autentica; un registro del servidor autoriza por emisor, sub y proyecto.
No se conecta Beta, Apps Script, Drive ni ningún cliente. No hay despliegue público.

Esta elección reduce infraestructura, pero NO verifica hosting remoto, acceso desde
dos equipos, concurrencia distribuida ni comunicación firmada Streamlit–Apps Script.
El equipo y su responsable están PENDIENTES de confirmación. El entorno remoto de
desarrollo no sustituye ese equipo: localhost debe corresponder al navegador que
efectúa el login. No abrir túneles ni puertos para resolver esta diferencia.

## Base comprobada y brecha

Base remota: `ebbee3ede4e57651c7569d70afe5d136083843b6`, rama
`experiment/creative-os-1-release-validation`. Evidencias conservadas:
`VALIDACION_LOCAL.txt` y `VALIDACION_MINIMA.txt`, 175/175 en cada entorno local.
La preparación inicial fue documental. La continuación funcional sí requirió
regresión: 196/196 aprobadas, como consta en `VALIDACION_PILOTO_OIDC_LOCAL.txt`.

COMPROBADO: `decision_demo.py` utiliza un selector de identidades ficticias; no es
un acceso Google. `decision_store.py` exige política del servidor. Los módulos de
sesiones y verificación son componentes aislados, todavía sin conexión a la UI.
El rango general `streamlit>=1.40,<2` admite versiones sin OIDC nativo.

PROPUESTO: entorno de piloto separado con Streamlit 1.67.0 (versión ya ensayada
localmente), Authlib compatible con esa versión y dependencias bloqueadas tras
revisión. No cambiar el rango general de Beta para preparar este piloto. La
disponibilidad y versión de Authlib siguen sin verificarse en el equipo de Puente.

IMPLEMENTADO LOCALMENTE: entrada independiente `pilot_oidc_app.py`, sin
selector de identidad, que vincule st.user a Actor y aplique la política en cada
operación del almacén, incluida lectura, exportación y consulta de auditoría.
No basta con pegar secretos en la demo. La entrada permanece apagada por defecto,
exige dirección de escucha local, Authlib y una base previamente inicializada como
piloto; no crea bases ni inicia login con configuración incompleta.

No combinar dos callbacks o gestores de cookies: el flujo OIDC nativo será el único
encargado del protocolo. `identity_boundary.py`/`session_store.py` no se consideran
integrados ni garantías adicionales hasta definir y probar su contrato real.
Comprobar state, nonce, validación de ID token y comportamiento PKCE en la versión
fijada; registrar lo observado, sin atribuir garantías a pruebas de otro adaptador.

## Recursos mínimos sujetos a autorización

| Recurso | Propuesta | Condición previa |
|---|---|---|
| Equipo de prueba | Un equipo de Puente; navegador local y disco protegido | Confirmar equipo y responsable |
| Google Cloud | Proyecto de laboratorio separado; reutilizar solo si se acredita aislamiento | Identificar proyecto exacto antes de modificarlo; existencia no verificada |
| OAuth | Un cliente web exclusivo del piloto; solo retorno localhost indicado | Autorizar creación o modificación nominal; no reutilizar credencial Beta |
| Identidades | Dos operadores consentidos y una identidad adicional para acceso denegado | Selección privada y consentimiento; no crear cuentas automáticamente |
| Permisos Google | Solo openid/email/profile para identidad; sin tokens expuestos ni acceso offline | Revisar consentimiento real; detener ante otros scopes |
| Datos | Proyectos SYNTH de los tres fixtures existentes | Copia aislada; ninguna conexión a datos reales |
| Persistencia | SQLite y backups fuera del checkout, con permisos del SO restringidos | Verificar ruta y recuperación en el equipo elegido |

No se ha comprobado la existencia de recursos OAuth reutilizables ni su facturación.
Objetivo: ningún servicio contratado, sin activar facturación. El piloto local no
necesita contratar hosting; no se certifica costo cero de recursos Cloud desconocidos.

## Identidad y autorización del servidor

Identidad canónica: (`https://accounts.google.com`, `sub`). No usar correo,
nombre, dominio ni parámetros del navegador como fuente de rol. Desconocido o
desactivado implica denegación por defecto, incluso si Google lo autenticó.

| Operador | Proyectos asignados | Acciones permitidas |
|---|---|---|
| Dirección/administración | Solo SYNTH expresamente asignados | Leer, guardar versión, revisar historial y aprobar/rechazar |
| Codirección/operación | Solo SYNTH expresamente asignados | Leer, guardar versión y revisar historial; sin aprobación final en este piloto |
| No registrado/desactivado | Ninguno | Ninguna |

La administración de usuarios queda fuera de la UI del piloto. Alta y desactivación
son operaciones controladas del responsable sobre el registro del servidor, con
evidencia. Proponer identidades no equivale a autorizarlas. Confirmar con dirección
si codirección requiere aprobar en un futuro; no inferir ese privilegio del nombre.

Bootstrap: observar el sub de cada cuenta tras login únicamente en una pantalla
de inscripción sin acceso a expedientes; responsable verifica correspondencia por
canal privado y registra alcance/rol autorizado. Nunca promover al primer usuario
que se conecte. No publicar correos, sub, credenciales ni capturas de consentimiento.

La cookie nativa de Streamlit persiste hasta 30 días y logout no cierra otras
sesiones existentes. Por ello el registro activo/permisos se consulta antes de
cada operación; no mantener una decisión de autorización en caché de sesión.
Se implementó un máximo operativo de 15 minutos desde iat, además de exp, verificado
en cada operación; no es el timeout de inactividad de SessionStore. El cierre
de sesión local no es revocación global Google. Incluir denegaciones en una bitácora
durable, sin tokens, con actor seudonimizado, acción, UTC, resultado e identificador
de prueba. La retención propuesta es hasta revisión y cierre de este piloto;
el responsable aprobará el borrado selectivo, nunca automático sobre otra base.

## Secuencia y aceptación

| ID | Comprobación real prevista | Criterio verificable |
|---|---|---|
| P00 | Aislamiento previo, sin login | Sin URLs Beta/Apps Script, conexiones de clientes ni secretos versionados; DB nueva exclusiva |
| P01 | Dirección entra por Google | Identidad derivada del proveedor; expediente sintético accesible solo con alta autorizada |
| P02 | Segundo operador y cuenta no registrada | Operación autorizada limitada; tercera identidad sin acceso aun si su login Google funciona |
| P03 | Acceso cruzado y aprobación | Proyecto no asignado y aprobación de operación denegados en servidor; evento durable |
| P04 | Nueva versión y duplicado | Aprobación obsoleta no habilita entrega; reintento no duplica decisión |
| P05 | Desactivación con sesión abierta | Siguiente acción y exportación denegadas en sesión y otra pestaña; no afirmar revocación global |
| P06 | Logout y expiración | Logout local efectivo; vencimiento operativo definido y comprobado; documentar otras pestañas |
| P07 | Reinicio del proceso | Expedientes/decisiones conservados en el mismo disco; reconexión vuelve a verificar permisos |
| P08 | Copia y restauración separada | Integridad y expedientes coinciden; prueba explícita de invalidación del acceso previo |
| P09 | Evaluación humana y recorrido | Dos operadores completan el flujo; dirección evalúa los tres dossiers y deja fundamento |

No ejecutar todos los casos como una macro ciega. Detener ante acceso indebido,
persistencia perdida, scopes inesperados o evidencia con secretos; conservar el
fallo sin corregir configuraciones Google automáticamente. Repetir solo el caso
afectado tras corrección revisada. Un caso no observado queda NO VERIFICADO.

Para P08: restaurar SQLite no borra la cookie OIDC nativa externa a esa base.
`restore_database` establece ahora un umbral de emisión; `NativePilotAccess` bloquea
claims iat anteriores incluso con una política ya creada. Probado con claims
simulados y una base restaurada. Sigue pendiente comprobar reautenticación y cookies
en el navegador real; no se atribuye esa evidencia al test de SessionStore.

Registro único propuesto: ID, versión de código/dependencias, fecha UTC, operador
seudonimizado, acción, esperado, observado, estado y evidencia saneada. Guardar
localmente fuera del repo durante el piloto y consolidar únicamente resultados sin
identificadores personales. No capturar URLs de callback ni pantallas con secretos.

## Acciones inmediatas y autorizaciones

1. Desarrollo aislado COMPLETADO para esta tanda: entrada OIDC, registro/política,
   auditoría de denegaciones, expiración y recuperación. 21 tests nuevos; regresión
   total 196/196 con Streamlit 1.67.0, Python 3.12.14 y criptografía obligatoria.
   st.user fue SIMULADO. Authlib NO está instalado; no se ejecutó callback real.
2. Revisión en Chat: confirmar equipo, responsables, alcance de los dos roles y
   cuentas consentidas por canal privado. Aprobar expresamente proyecto/cliente
   OAuth de laboratorio y almacenamiento seguro de secretos cuando se identifiquen.
3. Solo con lo anterior: configurar el recurso nominal autorizado y ejecutar el
   piloto real con datos ficticios. No abrir Beta ni Apps Script por extensión.
4. Volver a Chat con evidencia y dictamen. Aprobar este plan no aprueba producción.

Dictamen: APTO para revisión de la entrada local; NO APTO todavía para ejecutar login real
ni para integrar al núcleo. Pendientes: recursos autorizados, equipo y
aceptación humana. La prueba multiusuario remota y enlace firmado siguen pendientes
aunque este piloto local resulte satisfactorio.

## Preparación operativa posterior, no ejecutada

- Crear un entorno virtual y directorio de ejecución exclusivos en el equipo
  confirmado; instalar `requirements-pilot.txt` allí y guardar un inventario de
  versiones. No instalar ni configurar nada en Beta. Los rangos de dependencias
  aún no son un lockfile validado en ese equipo.
- Inicializar una base NUEVA mediante `NativePilotAccess` y dar de alta los sub
  verificados con `set_user`, solo bajo la autorización nominal pendiente. Es una
  API administrativa local, no una pantalla de alta. No hay autoinscripción ni
  promoción del primer usuario. La captura privada de sub para bootstrap sigue
  pendiente de acordar; no extraerla de correos ni pedir tokens.
- Almacenar secretos únicamente en la configuración local del entorno aprobado,
  nunca en Git/Chat. Campos [auth]: redirect_uri local indicado, cookie_secret
  aleatorio de al menos 32 caracteres, client_id, client_secret y metadata Google.
  No habilitar expose_tokens, client_kwargs, scopes adicionales ni acceso offline.
- Para el lanzamiento posterior, fijar `PUENTE_OIDC_PILOT_ENABLED=1` y
  `PUENTE_OIDC_PILOT_DB` a la ruta absoluta de esa base. Estos valores no se han
  configurado aquí. Comando preparado, NO ejecutado:

```bash
python -m streamlit run /RUTA/REVISADA/pilot_oidc_app.py --server.address=localhost --server.port=8501 --browser.gatherUsageStats=false --server.enableCORS=true --server.enableXsrfProtection=true
```

No copiar literalmente /RUTA/REVISADA. Verificar que no se hereda una configuración
global de otra aplicación. El endpoint de retorno vive solo en el equipo del piloto.
La entrada no ofrece exportaciones: evita enlaces persistentes de descarga que no
revaliden permisos. La entrega contractual al cliente continúa fuera de este paso.

Límites de seguridad: SQLite y su registro requieren permisos del sistema operativo;
los archivos nuevos del gate se crean con modo 0600 en POSIX, sin cifrado. Los
administradores de ese equipo pueden alterar la base; no se certifica resistencia
frente a ellos. No hay rate limiting ni validación distribuida. Cambios de permisos
se vuelven a consultar por operación, sin garantía transaccional frente a un cambio
administrativo concurrente; el alcance sigue siendo dos turnos en un equipo.

Revisión estática del Streamlit 1.67.0 instalado: el callback delega el intercambio
a Authlib y usa userinfo; su código activa PKCE S256 si el metadata lo anuncia.
Esta lectura NO verifica metadata real, state/nonce, firma, cookies ni PKCE en Google.

Fuentes oficiales consultadas el 2026-11-10:
- https://docs.streamlit.io/develop/concepts/connections/authentication
- https://developers.google.com/identity/openid-connect/openid-connect

04.01 ABIERTA — PRUEBA REAL NO INICIADA — 04.02 NO INICIADA.
