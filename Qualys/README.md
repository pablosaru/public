# Qualys API — Postman Collection

Colección de Postman con requests para interactuar con la API de Qualys, cubriendo autenticación JWT, gestión de tags y consultas a la Knowledge Base de vulnerabilidades.

## Requests incluidos

### Autenticación
| Método | Nombre | Descripción |
|--------|--------|-------------|
| POST | `Obtener JWT Token` | Obtiene un token JWT desde el gateway de Qualys |

### Asset Management — Tags
| Método | Nombre | Descripción |
|--------|--------|-------------|
| POST | `createStaticTagAplicativas` | Crea un tag estático para vulnerabilidades aplicativas |
| POST | `getIdTagAplicativas` | Busca el ID de un tag por nombre |
| POST | `addDynamicTagTomcat` | Crea un tag dinámico basado en regla de detección de vulnerabilidades (ejemplo: Nginx) |

### Knowledge Base
| Método | Nombre | Descripción |
|--------|--------|-------------|
| POST | `getSolutionByQID` | Consulta la KB por QID vía POST con body urlencoded |
| GET | `getSolutionByQID` | Consulta la KB por QID vía GET con parámetros en la URL |
| GET | `getSolutionByCVE-FAIL` | Consulta la KB por CVE (documentado como FAIL — la API no soporta este filtro directamente) |

## Configuración del environment

Antes de usar la colección, crear un environment en Postman con las siguientes variables:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `qualys_gateway` | URL del gateway de autenticación JWT | `gateway.qg1.apps.qualys.com` |
| `qualys_api_base_url` | URL base de la API v2 | `qualysapi.qg1.apps.qualys.com` |
| `qualys_web_base_url` | URL base del portal web | `qualysguard.qg1.apps.qualys.com` |

> Las URLs varían según la plataforma asignada (US1, US2, EU1, etc.). Verificar en **Help → About** dentro de Qualys.

### Autenticación

Los requests que usan **Basic Auth** toman las credenciales del environment de Postman. Configurar en la pestaña **Authorization** del environment (o a nivel colección):

- **Username**: usuario de Qualys
- **Password**: contraseña de Qualys

El request `Obtener JWT Token` usa credenciales en el body (`urlencoded`). Agregar al environment:

| Variable | Descripción |
|---|---|
| `qualys_username` | Usuario de Qualys |
| `qualys_password` | Contraseña de Qualys |

## Notas

- El request `getSolutionByCVE-FAIL` está documentado intencionalmente como fallo: la Knowledge Base API de Qualys no soporta búsqueda directa por CVE en ese endpoint. Se incluye como referencia
- Los tags dinámicos usan la API del portal (`portal-front/rest/assetview`) que es distinta a la API v2 (`qps/rest`) — requieren la variable `qualys_web_base_url` separada
- Los requests de Knowledge Base incluyen un QID de ejemplo (`361429`) y un CVE de ejemplo (`CVE-2025-47912`); reemplazarlos según la consulta

## Licencia

MIT