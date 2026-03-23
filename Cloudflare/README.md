# update_dns.py

Script de línea de comandos para gestionar registros DNS en Cloudflare. Permite listar, crear, actualizar y eliminar registros sin necesidad de entrar al dashboard.

## Requisitos

- Python 3.6+
- Sin dependencias externas (usa solo stdlib)
- Un [Cloudflare API Token](https://dash.cloudflare.com/profile/api-tokens) con permiso **Edit zone DNS**

## Instalación

```bash
# Clonar o copiar update_dns.py al directorio deseado
chmod +x update_dns.py

# Configurar el token (recomendado: agregar al .bashrc / .zshrc)
export CF_API_TOKEN="tu_token_aqui"
```

## Tipos de registro soportados

| Tipo  | Descripción              |
|-------|--------------------------|
| A     | Dirección IPv4           |
| TXT   | Texto (SPF, DMARC, etc.) |
| CNAME | Alias de dominio         |
| NS    | Nameserver               |

## Uso

```
python update_dns.py -d DOMINIO -t TIPO -n NAME [opciones]
```

### Parámetros

| Parámetro        | Descripción                                      |
|------------------|--------------------------------------------------|
| `-d`, `--domain` | Dominio principal (ej: `DOMINIO`)           |
| `-t`, `--type`   | Tipo de registro: `A`, `TXT`, `CNAME`, `NS`      |
| `-n`, `--name`   | Nombre del registro (ej: `_dmarc`, `www`, `@`)   |
| `-c`, `--content`| Valor del registro                               |
| `--list`         | Listar todos los registros del tipo/name         |
| `--delete`       | Eliminar el registro que coincida con `-c`       |
| `-k`, `--token`  | API Token (alternativa a la variable de entorno) |

---

## Ejemplos

### Listar registros

```bash
# Ver todos los NS de un subdominio
python update_dns.py -d DOMINIO -t NS -n subdominio --list

# Ver el registro DMARC actual
python update_dns.py -d DOMINIO -t TXT -n _dmarc --list
```

### Crear o actualizar

Si el registro **existe**, lo reemplaza. Si **no existe**, lo crea. En ambos casos imprime el valor anterior.

```bash
# Actualizar política DMARC
python update_dns.py -d DOMINIO -t TXT -n _dmarc -c "v=DMARC1; p=reject; rua=mailto:dmarc@DOMINIO"

# Crear o actualizar un A record
python update_dns.py -d DOMINIO -t A -n www -c "1.2.3.4"

# Crear o actualizar un CNAME
python update_dns.py -d DOMINIO -t CNAME -n mail -c "mail.example.com"

# Agregar un NS a un subdominio
python update_dns.py -d DOMINIO -t NS -n subdominio -c "ns1.example.com"
```

### Eliminar

`--delete` requiere `-c` para identificar exactamente qué registro borrar (especialmente útil cuando hay múltiples registros del mismo tipo, como NS).

```bash
# Eliminar un NS específico
python update_dns.py -d DOMINIO -t NS -n subdominio -c "ns1.example.com" --delete

# Eliminar registro de verificación de Google
python update_dns.py -d DOMINIO -t TXT -n @ -c "google-site-verification=xxxxx" --delete
```

---

## Salida esperada

```bash
# Actualización exitosa
ANTES  [TXT] _dmarc.DOMINIO → v=DMARC1; p=none; rua=mailto:dmarc@DOMINIO
AHORA  [TXT] _dmarc.DOMINIO → v=DMARC1; p=reject; rua=mailto:dmarc@DOMINIO  (ACTUALIZADO)

# Creación
ANTES  [A] nuevo.DOMINIO → (no existía)
AHORA  [A] nuevo.DOMINIO → 1.2.3.4  (CREADO)

# Eliminación
ANTES     [NS] subdominio.DOMINIO → ns1.example.com
ELIMINADO [NS] subdominio.DOMINIO → ns1.example.com

# Listado
Registros [NS] en subdominio.DOMINIO:
  → ns1.example.com
  → ns2.example.com
```

---

## Notas

- Los registros **TXT** se envían con comillas automáticamente, como requiere Cloudflare.
- Los registros **NS del apex** (`@`) no pueden eliminarse — Cloudflare los protege.
- Al crear/actualizar, se conservan el **TTL** y el estado **proxied** del registro original.
- El token puede pasarse con `-k` si no se quiere usar la variable de entorno.