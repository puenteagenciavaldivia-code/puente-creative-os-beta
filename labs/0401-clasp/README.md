# PUENTE Creative OS 04.01 · Recuperación del receptor con clasp

La etapa sigue abierta. La rama de referencia está en `3d9379e46563eaf6e33c5ee0a3ac2868ff747fce`. Su ejecución de [GitHub Actions](https://github.com/puenteagenciavaldivia-code/puente-creative-os-beta/actions/runs/44652180768) terminó correctamente. Se repitieron localmente las 45 pruebas de ese flujo (28 del motor, 14 de adjuntos y 3 de Streamlit). La suite Python completa pasó 224 pruebas con las dependencias de `requirements-test-oidc.txt`. Pasaron también las 6 pruebas Node de este directorio.

## Código disponible

Solo se encontró `apps_script.gs` en el historial alcanzable desde las ramas remotas revisadas. Es el receptor Beta y referencia una hoja fija. La rama de auditoría añade el cliente Python y el [contrato de aceptación](../../docs/0401-receptor-adjuntos-contrato.md). Faltan el código y el `appsscript.json` del proyecto aislado, su ID de Apps Script o un export revisado, y la configuración del laboratorio que identifique los recursos sintéticos y las cuentas de prueba. La descarga de clasp recupera código y manifiesto. Los permisos efectivos, propiedades de script y datos se revisan en Google por separado.

| Control | Observado localmente | Pendiente en Google Apps Script |
| --- | --- | --- |
| Duplicados | Beta reutiliza por nombre en un mismo envío, incluso si cambian los bytes. El cliente calcula una clave y guarda confirmaciones en sesión. | Clave durable por envío y adjunto, reintentos con otra sesión, carrera concurrente y rechazo de la misma clave con bytes distintos. |
| Interrupciones | El doble de Sheets falla al guardar el enlace tras crear el archivo. En el reintento, Beta encuentra ese archivo por nombre y guarda el enlace. | Reconciliación durable después de una interrupción y de un timeout tras confirmación. Comprobar recuento y hash en Drive. |
| Consentimiento | Streamlit exporta un booleano explícito. Beta acepta un adjunto para un envío conocido aunque el payload declare `files_consent: false`. | Denegar por consentimiento ausente o revocado según el estado del servidor y comprobar que no aparece ningún archivo ni vínculo. |
| Permisos y validación | Beta deniega un token incorrecto antes de abrir la hoja y rechaza un envío desconocido sin crear archivo. Acepta texto declarado como PDF. | Scopes efectivos, permisos de proyecto y Drive, revocación, aislamiento entre envíos y validación de contenido y límites. |
| Auditoría | Beta registra un enlace en la hoja. La ruta de adjuntos revisada carece de un registro durable de estados y eventos. | Evidencia de intentos, denegaciones, reconciliación y confirmación correlacionadas, con política de retención. |

## Recuperar el proyecto desde macOS

Codex ejecutó `clasp show-authorized-user` con clasp 3.4.1 y obtuvo `Not logged in.` Usa Node 22 o superior y una cuenta Google con acceso al código del proyecto aislado. En Apps Script, confirma el ID de secuencia de comandos en la configuración del proyecto y habilita la API en [Configuración de Apps Script](https://script.google.com/home/usersettings).

Desde la raíz de esta rama, ejecuta el siguiente bloque. La sesión OAuth se guarda temporalmente fuera del repositorio y se elimina al terminar. El navegador solicita consentimiento. Si la organización bloquea el acceso de clasp, el propietario puede exportar solo las fuentes y el manifiesto del laboratorio y entregarlos por un canal privado tras revisar su contenido.

```sh
(
  set -eu
  umask 077
  auth_dir=$(mktemp -d)
  trap 'rm -rf -- "$auth_dir"' EXIT
  export clasp_config_auth="$auth_dir/.clasprc.json"
  npm exec --yes --package=@google/clasp@3.4.1 -- clasp login
  printf 'ID del proyecto Apps Script 04.01 aislado: '
  read -r script_id
  node labs/0401-clasp/pull.mjs "$script_id"
)
```

El comando crea una configuración local con `rootDir: src` y descarga a un directorio nuevo bajo `.local/0401-clasp/`. Cada intento tiene su propio directorio y el comando requiere que la descarga contenga `appsscript.json`. El directorio y los archivos locales de configuración y autenticación de clasp están ignorados por Git. Comparte solo fuentes y manifiesto revisados, sin propiedades de script, credenciales, tokens, datos ni URLs privadas. Si no tienes esta rama en el Mac, el propietario también puede obtener los mismos dos insumos desde el editor de Apps Script.

## Validación siguiente

1. Revisar las fuentes recuperadas, el manifiesto, los scopes y la identidad de ejecución. Confirmar en Google que hojas, carpeta, cuentas y permisos pertenecen al laboratorio aislado y usan datos sintéticos.
2. Ejecutar los diez casos del contrato sobre ese receptor. Para los casos concurrentes y de interrupción, conservar el recuento en Drive, estado durable y resultados de ambos intentos. Para las denegaciones, medir la ausencia de efectos en Drive y Sheets. Para auditoría, guardar eventos y estados con identificadores sintéticos y sin secretos.
3. Registrar el commit o versión probada y las evidencias de la ejecución real. La etapa 04.01 sigue pendiente hasta completar esa validación.

Para repetir las comprobaciones locales desde la raíz:

```sh
python -m pip install -r requirements-test-oidc.txt
STREAMLIT_BROWSER_GATHER_USAGE_STATS=false python -m unittest discover -s tests
node --test labs/0401-clasp/*.test.mjs
```
