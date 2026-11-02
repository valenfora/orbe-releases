#!/usr/bin/env python3
"""Revisa los canales de canales.json una vez por día.

Canales 24 h de YouTube: si el directo no está al aire suma una falla; con 3 seguidas queda "caido".
Canales con web: la web tiene que responder 200. Los "programa" de YouTube no se revisan (no transmiten todo el día).
Escribe canales.json solo si algo cambió e imprime los ids que pasaron a caído (para abrir el issue).
"""
import json, re, sys, urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
LIMITE = 3

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "es-AR,es;q=0.9"})
    with urllib.request.urlopen(req, timeout=20) as r:
        return r.status, r.read(2_000_000).decode("utf-8", "replace")

def al_aire(c):
    try:
        if c.get("yt"):
            _, html = get(f"https://www.youtube.com/channel/{c['yt']}/live")
            return bool(re.search(r'"isLive(Now)?"\s*:\s*true', html))
        status, _ = get(c["web"])
        return status == 200
    except Exception:
        return False

def main(path):
    with open(path, encoding="utf-8") as f:
        doc = json.load(f)
    nuevos_caidos = []
    for c in doc["canales"]:
        if c.get("yt") and c.get("emision") != "24h":
            continue
        if al_aire(c):
            c.pop("fallas", None)
            c.pop("caido", None)
        else:
            c["fallas"] = c.get("fallas", 0) + 1
            if c["fallas"] >= LIMITE and not c.get("caido"):
                c["caido"] = True
                nuevos_caidos.append(c["id"])
    texto = "{\"v\":1,\"canales\":[\n" + ",\n".join(json.dumps(c, ensure_ascii=False, separators=(",", ":")) for c in doc["canales"]) + "\n]}\n"
    with open(path, encoding="utf-8") as f:
        viejo = f.read()
    if texto != viejo:
        with open(path, "w", encoding="utf-8") as f:
            f.write(texto)
    print(" ".join(nuevos_caidos))

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "canales.json")
