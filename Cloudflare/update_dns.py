#!/usr/bin/env python3
"""
Uso:
  python cf_dns.py -d DOMINIO -t TIPO -n NAME --list
  python cf_dns.py -d DOMINIO -t TIPO -n NAME -c CONTENT
  python cf_dns.py -d DOMINIO -t TIPO -n NAME -c CONTENT --delete

Ejemplos:
  python cf_dns.py -d DOMINIO -t NS  -n subdominio --list
  python cf_dns.py -d DOMINIO -t NS  -n subdominio -c "ns1.ejemplo.com" --delete
  python cf_dns.py -d DOMINIO -t TXT -n _dmarc -c "v=DMARC1; p=reject"
  python cf_dns.py -d DOMINIO -t A   -n www    -c "1.2.3.4"

Requiere: CF_API_TOKEN exportado en el entorno (o pasar con -k)
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.error

API = "https://api.cloudflare.com/client/v4"
VALID_TYPES = ("A", "TXT", "CNAME", "NS")


def cf_request(method, path, token, data=None):
    url = f"{API}{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, method=method, data=body, headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    })
    try:
        with urllib.request.urlopen(req) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return json.loads(e.read())


def die(msg):
    print(f"ERROR: {msg}", file=sys.stderr)
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Gestionar registros DNS en Cloudflare.")
    parser.add_argument("-d", "--domain",  required=True, help="Dominio (ej: DOMINIO)")
    parser.add_argument("-t", "--type",    required=True, choices=VALID_TYPES, help="Tipo: A | TXT | CNAME | NS")
    parser.add_argument("-n", "--name",    required=True, help="Name del registro (ej: _dmarc, www, @)")
    parser.add_argument("-c", "--content", default=None,  help="Valor/contenido del registro")
    parser.add_argument("--list",   action="store_true", help="Listar todos los registros del tipo/name")
    parser.add_argument("--delete", action="store_true", help="Eliminar el registro que coincida con -c")
    parser.add_argument("-k", "--token", default=os.environ.get("CF_API_TOKEN"), help="Cloudflare API Token")
    args = parser.parse_args()

    if not args.token:
        die("Token no encontrado. Exportá CF_API_TOKEN o usá -k TOKEN")
    if not args.list and not args.content:
        die("Especificá -c CONTENT, o usá --list para ver los registros existentes.")
    if args.delete and not args.content:
        die("--delete requiere -c CONTENT para identificar qué registro eliminar.")

    fqdn = args.domain if args.name == "@" else f"{args.name}.{args.domain}"

    # 1. Zone ID
    resp = cf_request("GET", f"/zones?name={args.domain}", args.token)
    if not resp.get("success") or not resp["result"]:
        die(f"Zona '{args.domain}' no encontrada.")
    zone_id = resp["result"][0]["id"]

    # 2. Buscar todos los registros del tipo/name
    resp = cf_request("GET", f"/zones/{zone_id}/dns_records?type={args.type}&name={fqdn}", args.token)
    if not resp.get("success"):
        die(resp["errors"][0]["message"])
    records = resp["result"]

    # 3. --list
    if args.list:
        if not records:
            print(f"No hay registros [{args.type}] para {fqdn}")
        else:
            print(f"Registros [{args.type}] en {fqdn}:")
            for r in records:
                print(f"  → {r['content']}")
        return

    # 4. Buscar coincidencia exacta por content (para NS y duplicados)
    match = next((r for r in records if r["content"] == args.content), None)

    # 5. --delete
    if args.delete:
        if not match:
            die(f"No existe [{args.type}] {fqdn} → {args.content}")
        print(f"ANTES     [{match['type']}] {match['name']} → {match['content']}")
        resp = cf_request("DELETE", f"/zones/{zone_id}/dns_records/{match['id']}", args.token)
        if resp.get("success"):
            print(f"ELIMINADO [{match['type']}] {match['name']} → {match['content']}")
        else:
            die(resp["errors"][0]["message"])
        return

    # 6. Crear o reemplazar (toma el primero si hay múltiples)
    existing = records[0] if records else None
    if existing:
        print(f"ANTES  [{existing['type']}] {existing['name']} → {existing['content']}")
    else:
        print(f"ANTES  [{args.type}] {fqdn} → (no existía)")

    content = f'"{args.content}"' if args.type == "TXT" else args.content
    payload = {
        "type":    args.type,
        "name":    fqdn,
        "content": content,
        "ttl":     existing["ttl"] if existing else 1,
        "proxied": existing["proxied"] if existing else False,
    }

    if existing:
        resp = cf_request("PUT", f"/zones/{zone_id}/dns_records/{existing['id']}", args.token, payload)
        action = "ACTUALIZADO"
    else:
        resp = cf_request("POST", f"/zones/{zone_id}/dns_records", args.token, payload)
        action = "CREADO"

    if resp.get("success"):
        r = resp["result"]
        print(f"AHORA  [{r['type']}] {r['name']} → {r['content']}  ({action})")
    else:
        die(resp["errors"][0]["message"])


if __name__ == "__main__":
    main()