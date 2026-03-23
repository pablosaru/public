# n8n — DMARC RUA Report Analyzer

Workflow de n8n que procesa automáticamente los reportes RUA de DMARC recibidos por email, parsea el XML, analiza los resultados con IA y envía un informe HTML por correo.

## ¿Qué hace?

1. **Lee los emails** de la carpeta de reportes DMARC en Outlook con adjuntos recibidos en las últimas 24 horas
2. **Descarga y descomprime** el adjunto (`.zip` o `.gz` con el XML adentro)
3. **Parsea el XML** del reporte RUA extrayendo dominio, política, rango de fechas, IPs, resultados SPF/DKIM y cantidad de emails afectados
4. **Agrega** todos los reportes del día en un único payload
5. **Analiza con Claude** (Anthropic) y genera un informe HTML con resumen ejecutivo, estado por dominio, IPs con fallos y recomendaciones priorizadas
6. **Envía el informe** por email vía Outlook

## Flujo de nodos

```
Manual Trigger
    └── Get Many Messages (Outlook)
            └── Loop Over Items Mail
                    ├── [batch completo] → Aggregate → Basic LLM Chain (Claude) → Send Email
                    └── [cada mail] → Get Attachments → getAttach0 → Download Attachment
                                            └── Decompress → Extract from File → parserXML
                                                    └── Loop Over Items Mail (feedback)
```

## Antes de importar el workflow

El JSON fue sanitizado. Antes de importarlo en tu instancia de n8n, reemplazá los siguientes valores:

| Campo | Placeholder | Reemplazar por |
|---|---|---|
| Credencial Anthropic | `YOUR_ANTHROPIC_CREDENTIAL_ID` | ID de tu credencial Anthropic en n8n |
| Credencial Outlook | `YOUR_OUTLOOK_CREDENTIAL_ID` | ID de tu credencial Outlook en n8n |
| Carpeta Outlook | `YOUR_OUTLOOK_FOLDER_ID` | ID de la carpeta donde llegan los RUA |
| Email destinatario | `your@email.com` | Email que recibe el informe diario |

> Los IDs de credenciales de n8n los encontrás en **Settings → Credentials** de tu instancia.  
> Para obtener el ID de la carpeta de Outlook, ejecutá el nodo **Get Many Messages** sin filtro de carpeta y revisá el campo `parentFolderId` en cualquier email recibido.

## Requisitos

- n8n con acceso a internet
- Cuenta de **Microsoft Outlook** con OAuth2 configurado en n8n
- Cuenta de **Anthropic** con API key configurada en n8n
- Carpeta en Outlook donde llegan los reportes RUA

## Configuración

### 1. Credenciales necesarias en n8n

| Credencial | Nodo | Descripción |
|---|---|---|
| `Microsoft Outlook OAuth2` | Get Many Messages, Get many attachments, Download an attachment, Send a message | Cuenta que recibe los RUA y envía el informe |
| `Anthropic API` | Anthropic Chat Model1 | Clave de API de Anthropic para Claude |

### 2. Ventana de tiempo

Por defecto el workflow busca emails recibidos **ayer** (últimas 24 horas). Está configurado en el nodo **Get Many Messages**:

```javascript
receivedAfter:  $now.minus({days:1}).startOf('day').toISO()
receivedBefore: $now.minus({days:0}).startOf('day').toISO()
```

Ajustar según la frecuencia de ejecución deseada.

## Activación

El workflow tiene un **Manual Trigger**. Para automatizarlo, reemplazarlo por un nodo **Schedule Trigger** configurado para ejecutarse cada mañana (ej: 08:00 AM).

## Informe generado

El informe HTML enviado por email incluye:

- Rango de fechas analizadas
- Resumen ejecutivo con totales
- Estado por dominio (política DMARC activa)
- IPs con fallos SPF/DKIM y emails afectados
- Recomendaciones con prioridad (🔴 crítico / 🟡 medio / 🟢 bajo)

## Notas técnicas

- El parser XML está implementado en JavaScript nativo dentro de n8n, sin librerías externas
- El workflow maneja adjuntos comprimidos en `.zip` o `.gz`; si los reportes llegan en otro formato hay que ajustar el nodo **Decompress**
- Solo procesa el **primer adjunto** de cada email (`items[0]`). Si un email trae múltiples XMLs, se ignoran los demás
- El modelo usado es `claude-sonnet-4-6`

## Licencia

MIT