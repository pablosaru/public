# Qualys Patch Job — SSH Hardening: PermitRootLogin

## Descripción

Job de Qualys Patch Management que aplica hardening de SSH deshabilitando el login directo como root (`PermitRootLogin no`) en sistemas Linux. Se ejecuta como parte del ciclo de parcheo mediante una pre-action y una post-action.

---

## Controles corregidos

| Control ID | Descripción |
|------------|-------------|
| **26772** | Status of 'PermitRootLogin' specified in '/etc/ssh/sshd_config.d/*.conf' files |
| **2239**  | Status of the 'PermitRootLogin' setting in the 'sshd_config' file |

---

## Compatibilidad

| Sistema operativo | Versión         | Probado |
|-------------------|-----------------|---------|
| AlmaLinux         | 8.x / 9.x       | ✓       |

> En AlmaLinux 9, `PermitRootLogin` puede ya venir configurado en `no` o `prohibit-password` por defecto. En ese caso, la pre-action no realiza cambios.

---

## Estructura del Job

### Pre-action: `ChangePermitRootLoginToNO`

Busca y reemplaza `PermitRootLogin yes` por `PermitRootLogin no` en los archivos de configuración de SSH.

**Archivos evaluados:**
- `/etc/ssh/sshd_config`
- `/etc/ssh/sshd_config.d/*.conf`

**Comportamiento:**
- Genera un backup del archivo antes de modificarlo (`<archivo>.bak`)
- Registra el resultado en `/var/log/messages` bajo la etiqueta `sshd-hardening`
- Si no encuentra cambios necesarios, lo registra y continúa sin modificar nada
- Si no encuentra ningún archivo de configuración, falla con error

```bash
#!/bin/bash

set -euo pipefail

log() { logger -t sshd-hardening "$1"; }

[[ $EUID -ne 0 ]] && { log "ERROR: requiere root."; exit 1; }

FILES=()
[[ -f /etc/ssh/sshd_config ]] && FILES+=(/etc/ssh/sshd_config)

while IFS= read -r -d '' f; do
    FILES+=("$f")
done < <(find /etc/ssh/sshd_config.d -maxdepth 1 -type f -name "*.conf" -print0 2>/dev/null)

[[ ${#FILES[@]} -eq 0 ]] && { log "ERROR: no se encontraron archivos de configuración."; exit 1; }

for f in "${FILES[@]}"; do
    if grep -qiE '^\s*PermitRootLogin\s+yes' "$f"; then
        cp "$f" "${f}.bak"
        sed -i -E 's/^(\s*PermitRootLogin\s+)yes/\1no/Ig' "$f"
        log "OK: PermitRootLogin cambiado a no en $f"
    else
        log "OK: sin cambios necesarios en $f"
    fi
done
```

---

### Post-action: `Restart sshd`

Recarga el servicio `sshd` para aplicar la configuración modificada.

**Comportamiento:**
- Intenta `systemctl reload sshd` primero (sin cortar sesiones activas)
- Si falla, ejecuta `systemctl restart sshd`
- Registra el resultado en `/var/log/messages` bajo la etiqueta `sshd-hardening`

```bash
#!/bin/bash

set -euo pipefail

log() { logger -t sshd-hardening "$1"; }

if systemctl reload sshd 2>/dev/null || systemctl restart sshd; then
    log "OK: sshd recargado correctamente"
else
    log "ERROR: fallo al recargar sshd"
    exit 1
fi
```

---

## Logs

Ambos scripts escriben en `/var/log/messages` con la etiqueta `sshd-hardening`. Ejemplo de salida real:

```
Mar 23 17:26:38 SERVER01 sshd-hardening[2439702]: OK: sin cambios necesarios en /etc/ssh/sshd_config
Mar 23 17:26:38 SERVER01 sshd-hardening[2439704]: OK: sin cambios necesarios en /etc/ssh/sshd_config.d/50-redhat.conf
Mar 23 17:26:38 SERVER01 sshd-hardening[2439708]: OK: PermitRootLogin cambiado a no en /etc/ssh/sshd_config.d/01-permitrootlogin.conf
Mar 23 17:26:40 SERVER01 systemd[1]: Reloading OpenSSH server daemon...
Mar 23 17:26:40 SERVER01 systemd[1]: Reloaded OpenSSH server daemon.
Mar 23 17:26:40 SERVER01 sshd-hardening[2439735]: OK: sshd recargado correctamente
```

Para consultar los logs del job:

```bash
grep sshd-hardening /var/log/messages
# o bien:
journalctl -t sshd-hardening
```

---

## Verificación post-ejecución

Para confirmar que la configuración efectiva fue aplicada correctamente:

```bash
sshd -T | grep -i permitrootlogin
```

La salida esperada es:

```
permitrootlogin no
```

---

## Notas

- El backup de cada archivo modificado queda en `<archivo>.bak` en el mismo directorio.
- El agente de Qualys ejecuta los scripts como root, por lo que no se requiere configuración adicional de permisos.
- `reload` es preferible a `restart` ya que no interrumpe sesiones SSH activas en el momento de la ejecución.