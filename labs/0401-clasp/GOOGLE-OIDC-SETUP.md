# Puente Creative OS · 04.01 · Conexión Google OIDC

Estado: **preparación ejecutable, sin autorización real de usuarios**. Este proyecto NO reutiliza el login de `clasp` como credencial de Creative OS. No se deben enviar ID tokens, refresh tokens, contraseñas ni secretos por chat ni a GitHub.

## Fuentes verificadas
- [Google — verificación backend](https://developers.google.com/identity/sign-in/web/backend-auth)
- [Google OIDC Discovery](https://accounts.google.com/.well-known/openid-configuration)
- [Google — OpenID Connect](https://developers.google.com/identity/openid-connect/openid-connect)

Google usa `https://accounts.google.com` como issuer habitual, `https://www.googleapis.com/oauth2/v3/certs` para JWKS y rota las claves según las cabeceras de caché. El backend **debe** verificar firma, `aud`, `iss`, `exp` y acceso a cliente/proyecto en la fuente propia de Puente.

## Código disponible
- `oidc-verifier.mjs`: validador RS256, issuer/audience/exp/iat/nbf.
- `google-identity-adapter.mjs`: descarga JWKS solo del endpoint oficial de Google, limita tamaño y TTL de caché, falla cerrado cuando Google está indisponible.
- `google-identity-adapter.test.mjs`: casos sintéticos con claves RSA efímeras, sin cuentas ni tokens reales.
- `upload-gateway.mjs`: espera `verifyIdentity`, `findSubmission` y `membershipsFor` de un backend confiable. No se ha conectado a una base de datos ni a un login real.

## Autorización inicial necesaria
1. En Google Cloud Console, crear/seleccionar un **proyecto OAuth de pruebas**, separado de Apps Script y del proyecto de operación.
2. Configurar la pantalla de consentimiento y añadir **solo usuarios de prueba autorizados**; no publicar externamente la aplicación.
3. Crear un cliente OAuth con el tipo correspondiente al frontend real de pruebas (normalmente `Aplicación web`). Registrar orígenes y redirecciones exactos de un servicio privado que **exista**: no inventar localhost ni URLs productivas.
4. Guardar el **OAuth Client ID** en la configuración privada del servidor que autenticará los usuarios; no enviarlo al receptor GAS. Guardar cualquier secreto solo en el gestor de secretos. El Client ID no es un secreto, pero no autoriza acceso por sí mismo.
5. Implementar en un backend privado el flujo de inicio de sesión Google compatible con OAuth/OIDC, comprobar `state`, `nonce` y PKCE según flujo; recibir ID token por HTTPS; validar con `google-identity-adapter`; resolver directorio de roles/cliente desde servidor.
6. Probar con dos **identidades sintéticas de laboratorio** de ámbitos distintos; negar acceso cruzado. Rotación JWKS, expiración y revocación requieren evidencias adicionales.
7. No desplegar webhook GAS ni habilitar archivos de clientes hasta revisar G03–G09 del cierre.

## Importante
- La API de Apps Script habilitada y el login de `clasp` **no crean una aplicación OAuth de Creative OS**.
- No usar correo electrónico como identificador de rol: usar `sub` Google verificado y una tabla de membresías propia. El `hd` de Google ayuda con cuentas Workspace, pero no es la autorización del cliente/briefing.
- Se requiere backend real para conservar la sesión, verificar revocaciones y emitir autorización limitada. El adaptador actual es un módulo aislado sin ese backend.
- No hay pruebas de usuarios Google reales ni evidencia de un token ID real verificado. **G05 sigue pendiente** hasta hacerlo.
- CI de GitHub de la rama laboratorio debe inspeccionarse antes de declarar las pruebas aprobadas; la existencia de archivos de tests no implica su éxito.
