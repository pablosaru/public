import os
import requests
import certifi_win32
import json
import xml.etree.ElementTree as ET
import csv
import re
import sys
import time
import random
from datetime import datetime, timezone

QUALYS_USER = os.getenv("QUALYS_USER")
QUALYS_PASS = os.getenv("QUALYS_PASS")

def crear_session():
    session = requests.Session()

    session.headers.update({
        "User-Agent": "PostmanRuntime/7.32.3",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    })

    session.auth = (QUALYS_USER, QUALYS_PASS)
    #session.verify = False

    session.headers.update({
        "User-Agent": "PostmanRuntime/7.32.3",
        "Accept": "*/*",
        "Cookie": "QualysSession=c167d742cc96dc9a61f59ae913637def; Path=/; Secure; HttpOnly;"
    })

    print("Cookies:", session.cookies.get_dict())
    return session

def obtener_vulnerabilidades(session, tag="Apache"):
    tag_encoded = tag.replace(" ", "%20")

    base_url = "https://qualysguard.qg3.apps.qualys.com/portal-front/rest/assetview/1.0/assetvuln/v2"

    offset = 0
    limit = 25
    resultado = []

    headers = {
        "X-Requested-With": "Postman",
        "Content-Type": "application/json",        
        "User-Agent": "PostmanRuntime/7.32.3",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "host": "qualysguard.qg3.apps.qualys.com",
        "referer": "https://qualysguard.qg3.apps.qualys.com/vm/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.0.0 Safari/537.36 Edg/148.0.0.0"
    }

    while True:        
        print(f"[INFO] Tag={tag} | offset={offset} | limit={limit}")

        params = {
            "limit": limit,
            "offset": offset,
            "fields": "qid,title,assetName",
            "query": "not (tags.name:`Defectuosos` or tags.name:`Excluidos` or tags.name:`EOS`)",
            "havingQuery": f"(vulnerabilities.tags.name:`{tag_encoded}` and vulnerabilities.detectionScore:[70 ... 100] and not vulnerabilities.tags.name:`mitigada`) "
                        f"and (vulnerabilities.typeDetected:[Confirmed, Potential] and vulnerabilities.found:TRUE and vulnerabilities.disabled:FALSE and vulnerabilities.ignored:FALSE)",
            "includeAssets": "true"
        }

 #       response = session.get(base_url, params=params, verify=False, timeout=60, allow_redirects=False)
        response = session.get(base_url, params=params, timeout=60, allow_redirects=False)

        time.sleep(1 + random.uniform(0.5, 1.5))


        if response.status_code == 302:
            print(f"[WARN] Redirect detectado (posible bloqueo o límite). Reintentando offset={offset}...")
            time.sleep(5 + random.uniform(2,5))
            continue

        if response.status_code != 200:
            raise Exception(f"[ERROR] HTTP {response.status_code}: {response.text}")


        if not response.text.strip():
            print(f"[WARN] Respuesta vacía en offset={offset}")
            break

        try:
            data = response.json()
        except Exception:
            raise Exception(f"[ERROR] Respuesta no es JSON:\n{response.text[:500]}")

        if not data:
            print(f"[INFO] Sin más datos en offset={offset}")
            break

        for item in data:
            resultado.append({
                "qid": item.get("qid"),
                "title": item.get("title"),
                "assetName": item.get("assetName"),
                "Solution": "",
                "PUBLISHED_DATETIME": ""
            })

        if len(data) < limit:
            break

        offset += limit

    return resultado



def obtener_soluciones(session, resultado):
    # Obtener QIDs únicos
    qids_unicos = { str(item.get("qid")) for item in resultado if item.get("qid") }
    strQid = ",".join(qids_unicos)

    urlkb = "https://qualysapi.qg3.apps.qualys.com/api/2.0/fo/knowledge_base/vuln/"
    params = {
        "action": "list",
        "ids": strQid,
        "details": "All"
    }
    headers = {
        "X-Requested-With": "Postman",
        "Content-Type": "application/x-www-form-urlencoded",
        "User-Agent": "PostmanRuntime/7.32.3",
        "Accept": "*/*",
        "Connection": "keep-alive",
        "Accept-Encoding": "gzip, deflate, br"
    }

    # response_kb = requests.post(urlkb, auth=(QUALYS_USER, QUALYS_PASS), headers=headers, params=params, verify=False, timeout=60)
    #response_kb = requests.post(urlkb, auth=(QUALYS_USER, QUALYS_PASS), headers=headers, params=params, timeout=60)
    response_kb = session.post(urlkb, auth=(QUALYS_USER, QUALYS_PASS), headers=headers, params=params, timeout=60)

    time.sleep(1 + random.uniform(0.5, 1.5))

    kb_data = response_kb.text
    root = ET.fromstring(kb_data)

    qid_to_data = {}
    for vuln in root.findall(".//VULN"):
        qid = vuln.findtext("QID")
        solution = vuln.findtext("SOLUTION")
        published = vuln.findtext("PUBLISHED_DATETIME")

        if qid:
            qid_to_data[qid] = {
                "Solution": solution,
                "PUBLISHED_DATETIME": published
            }

    # Enriquecer resultado con soluciones
    for item in resultado:
        qid = str(item["qid"])
        kb_info = qid_to_data.get(qid, {})
        item["Solution"] = kb_info.get("Solution", "")
        item["PUBLISHED_DATETIME"] = kb_info.get("PUBLISHED_DATETIME", "")

    return resultado


def _parse_dt(dt_str: str) -> datetime:
    """
    Convierte '2025-10-22T01:15:17Z' a datetime timezone-aware.
    Si viene vacío o inválido, devuelve datetime mínimo (para no ganar jamás).
    """
    if not dt_str:
        return datetime.min.replace(tzinfo=timezone.utc)

    # Formato típico de Qualys KB: 2017-01-18T00:43:30Z
    try:
        return datetime.strptime(dt_str, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        # fallback: ISO con offset
        try:
            return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except Exception:
            return datetime.min.replace(tzinfo=timezone.utc)

def resumir_por_asset(resultado_completo):
    """
    Devuelve un resumen por assetName:
    - un registro por asset
    - elige el que tenga mayor PUBLISHED_DATETIME
    - conserva assetName, qid, Solution (y opcional la fecha)
    """
    mejor_por_asset = {}

    for item in resultado_completo:
        asset = item.get("assetName")
        if not asset:
            continue

        dt_item = _parse_dt(item.get("PUBLISHED_DATETIME"))

        if asset not in mejor_por_asset:
            mejor_por_asset[asset] = item
        else:
            dt_actual = _parse_dt(mejor_por_asset[asset].get("PUBLISHED_DATETIME"))
            if dt_item > dt_actual:
                mejor_por_asset[asset] = item

    # Armamos salida resumida (solo qid+solution por asset)
    resultado_resumido = []
    for asset, item in mejor_por_asset.items():
        resultado_resumido.append({
            "assetName": asset,
            "qid": item.get("qid"),
            "Solution": item.get("Solution", ""),
            # si NO querés la fecha, podés borrar esta línea
            "PUBLISHED_DATETIME": item.get("PUBLISHED_DATETIME", "")
        })

    # opcional: ordenar por assetName para que el CSV quede prolijo
    resultado_resumido.sort(key=lambda x: (x["assetName"] or ""))

    return resultado_resumido

def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "Apache"

    session1 = crear_session()
    resultado = obtener_vulnerabilidades(session1, tag)

    session2 = crear_session()
    resultado_completo = obtener_soluciones(session2, resultado)

    resultado_resumido = resumir_por_asset(resultado_completo)
    
    tag_safe = re.sub(r'[^a-zA-Z0-9_-]', '_', tag)
    csv_file = f"qualys_vulns_resumido_{tag_safe}.csv"
    with open(csv_file, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=["assetName", "qid", "Solution", "PUBLISHED_DATETIME"])
        writer.writeheader()
        writer.writerows(resultado_resumido)

    print(f"CSV generado: {csv_file}")



if __name__ == "__main__":
    main()