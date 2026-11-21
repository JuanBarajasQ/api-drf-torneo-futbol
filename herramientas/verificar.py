#!/usr/bin/env python3
"""
Verificador del contrato mínimo de la API.

Uso:
    python herramientas/verificar.py https://tu-api.onrender.com
    python herramientas/verificar.py https://tu-api.onrender.com --repo .

Revisa tu API desplegada leyendo su propio esquema OpenAPI (/api/schema/),
así que funciona con cualquier dominio. Con --repo revisa además la carpeta
de evidencias y la colección de tu cliente de APIs.

Solo usa la biblioteca estándar de Python: no hay que instalar nada.
"""
import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VERDE, ROJO, AMARILLO, GRIS, FIN = "\033[32m", "\033[31m", "\033[33m", "\033[90m", "\033[0m"
resultados = []


def ok(titulo, detalle=""):
    resultados.append(True)
    print(f"{VERDE}✔{FIN} {titulo}" + (f" {GRIS}· {detalle}{FIN}" if detalle else ""))


def falla(titulo, detalle=""):
    resultados.append(False)
    print(f"{ROJO}✘ {titulo}{FIN}" + (f"\n    {detalle}" if detalle else ""))


def aviso(texto):
    print(f"{AMARILLO}!{FIN} {texto}")


def pedir(url, metodo="GET", cuerpo=None, timeout=30, acepta="application/json"):
    """Devuelve (código, encabezados, texto). No lanza excepción por 4xx/5xx."""
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(url, data=datos, method=metodo)
    req.add_header("Accept", acepta)
    req.add_header("User-Agent", "verificador-api-drf")
    if datos is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, dict(r.headers), r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), e.read().decode("utf-8", "replace")


def como_json(texto):
    try:
        return json.loads(texto)
    except ValueError:
        return None


def despertar(base):
    """Render apaga el servicio gratis tras 15 minutos sin uso; tarda cerca de un minuto en volver."""
    for intento in range(1, 5):
        try:
            codigo, _, _ = pedir(f"{base}/api/", timeout=60)
            return codigo
        except Exception as e:  # tiempo agotado, DNS, conexión
            aviso(f"Intento {intento}: la API no responde todavía ({e.__class__.__name__}). Esperando…")
            time.sleep(10)
    return None


def main():
    ap = argparse.ArgumentParser(description="Verifica el contrato mínimo de tu API.")
    ap.add_argument("url", help="URL pública de tu API, por ejemplo https://mi-api.onrender.com")
    ap.add_argument("--repo", help="ruta a tu repositorio para revisar evidencias y colección")
    args = ap.parse_args()
    base = args.url.rstrip("/")
    if base.endswith("/api"):
        base = base[:-4]

    print(f"\nVerificando {base}\n")

    # 1. ¿Responde?
    codigo = despertar(base)
    if codigo is None:
        falla("La API responde en /api/", "No hubo respuesta después de varios intentos. Revisa el log de Render.")
        return resumen()
    if codigo != 200:
        falla("La API responde en /api/", f"Respondió {codigo}. Revisa que el router esté incluido en config/urls.py.")
        return resumen()
    ok("La API responde en /api/")

    # 2. Raíz del router
    _, _, texto = pedir(f"{base}/api/")
    raiz = como_json(texto)
    recursos = {}
    if isinstance(raiz, dict):
        recursos = {k: v for k, v in raiz.items() if isinstance(v, str) and v.startswith("http")}
    if len(recursos) >= 3:
        ok("La raíz lista al menos 3 recursos", ", ".join(recursos))
    else:
        falla("La raíz lista al menos 3 recursos",
              f"Encontré {len(recursos)}. ¿Usas DefaultRouter y registraste los tres ViewSets?")

    # 3. DEBUG apagado
    codigo, _, texto = pedir(f"{base}/esta-ruta-no-existe-xyz/")
    if codigo == 404 and "URLconf" not in texto and "Traceback" not in texto:
        ok("DEBUG está desactivado en producción")
    else:
        falla("DEBUG está desactivado en producción",
              "La página de error muestra detalles internos. En Render no definas DEBUG=True.")

    # 4. Esquema OpenAPI
    codigo, _, texto = pedir(f"{base}/api/schema/?format=json")
    esquema = como_json(texto) if codigo == 200 else None
    rutas = (esquema or {}).get("paths", {})
    if rutas:
        ok("El esquema OpenAPI se publica en /api/schema/", f"{len(rutas)} rutas")
    else:
        falla("El esquema OpenAPI se publica en /api/schema/", f"Respondió {codigo}.")

    # 5. Swagger
    codigo, _, texto = pedir(f"{base}/api/docs/", acepta="text/html")
    if codigo == 200 and "swagger" in texto.lower():
        ok("La documentación Swagger carga en /api/docs/")
    else:
        falla("La documentación Swagger carga en /api/docs/", f"Respondió {codigo}.")

    # 6. Listas paginadas
    sin_paginar = []
    for nombre, url in recursos.items():
        codigo, _, texto = pedir(url)
        datos = como_json(texto)
        if not (codigo == 200 and isinstance(datos, dict) and {"count", "next", "previous", "results"} <= set(datos)):
            sin_paginar.append(nombre)
    if recursos and not sin_paginar:
        ok("Todas las listas vienen paginadas", "count, next, previous y results")
    elif recursos:
        falla("Todas las listas vienen paginadas",
              f"Sin paginar o con error: {', '.join(sin_paginar)}. Configura DEFAULT_PAGINATION_CLASS y PAGE_SIZE.")

    # Clasificar rutas del esquema
    api_rutas = [r for r in rutas if r.startswith("/api/") and not r.startswith(("/api/schema", "/api/docs"))]
    patron_lista = re.compile(r"^/api/[^/{}]+/$")
    patron_detalle = re.compile(r"^/api/[^/{}]+/\{[^}]+\}/$")
    acciones = [r for r in api_rutas if not patron_lista.match(r) and not patron_detalle.match(r)]
    acciones_detalle = [r for r in acciones if "{" in r]

    # 7. Filtros, búsqueda y orden
    mejor = None
    for r in api_rutas:
        if not patron_lista.match(r):
            continue
        get = rutas[r].get("get", {})
        nombres = {p.get("name") for p in get.get("parameters", []) if p.get("in") == "query"}
        otros = nombres - {"page", "page_size", "limit", "offset", "search", "ordering", "format"}
        if "search" in nombres and "ordering" in nombres and otros:
            mejor = (r, sorted(otros))
            break
    if mejor:
        ok("Un recurso tiene filtros, búsqueda y orden", f"{mejor[0]} · filtros: {', '.join(mejor[1])}")
    else:
        falla("Un recurso tiene filtros, búsqueda y orden",
              "Ningún listado declara a la vez ?search=, ?ordering= y al menos un filtro.")

    # 8. Acciones propias
    if len(acciones) >= 2 and acciones_detalle:
        ok("Hay al menos dos @action y una es de detalle", ", ".join(acciones))
    else:
        falla("Hay al menos dos @action y una es de detalle",
              f"Encontré: {', '.join(acciones) or 'ninguna'}.")

    # 9. Validación: un POST vacío debe responder 400 con errores por campo
    con_post = [r for r in api_rutas if patron_lista.match(r) and "post" in rutas[r]]
    respuestas_400 = 0
    for r in con_post:
        codigo, _, texto = pedir(f"{base}{r}", "POST", {})
        datos = como_json(texto)
        if codigo == 400 and isinstance(datos, dict) and any(isinstance(v, list) for v in datos.values()):
            respuestas_400 += 1
    if con_post and respuestas_400 == len(con_post):
        ok("Un POST vacío responde 400 con errores por campo", f"{respuestas_400} recursos")
    elif con_post:
        falla("Un POST vacío responde 400 con errores por campo",
              f"Solo {respuestas_400} de {len(con_post)} recursos. Revisa los campos obligatorios.")
    else:
        falla("Un POST vacío responde 400 con errores por campo", "Ningún listado acepta POST.")

    # 10. Enlaces con https
    if recursos:
        _, _, texto = pedir(next(iter(recursos.values())))
        datos = como_json(texto) or {}
        siguiente = datos.get("next") if isinstance(datos, dict) else None
        if siguiente and not siguiente.startswith("https://") and base.startswith("https://"):
            aviso("Los enlaces de paginación salen con http://. Revisa SECURE_PROXY_SSL_HEADER en settings.py.")

    # 11. Repositorio
    if args.repo:
        revisar_repo(Path(args.repo))

    return resumen()


EVIDENCIAS = ["01", "02", "03", "04", "05", "06", "07"]


def revisar_repo(repo):
    print()
    carpeta = repo / "evidencias"
    imagenes = [p.name for p in carpeta.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}]
    faltan = [n for n in EVIDENCIAS if not any(img.startswith(n) for img in imagenes)]
    if not faltan:
        ok("La carpeta evidencias/ tiene las 7 capturas", f"{len(imagenes)} imágenes")
    else:
        falla("La carpeta evidencias/ tiene las 7 capturas", f"Faltan las que empiezan por: {', '.join(faltan)}")

    col = repo / "colecciones"
    bruno = list(col.rglob("*.bru"))
    otros = [p for p in col.rglob("*") if p.suffix.lower() in {".json", ".yaml", ".yml"}]
    if bruno or otros:
        ok("La colección del cliente de APIs está en colecciones/",
           f"{len(bruno)} peticiones de Bruno" if bruno else f"{len(otros)} archivos exportados")
    else:
        falla("La colección del cliente de APIs está en colecciones/",
              "No encontré archivos .bru ni una exportación .json o .yaml.")


def resumen():
    total, bien = len(resultados), sum(resultados)
    color = VERDE if bien == total else (AMARILLO if bien >= total / 2 else ROJO)
    print(f"\n{color}{bien} de {total} verificaciones pasaron.{FIN}\n")
    return 0 if bien == total else 1


if __name__ == "__main__":
    sys.exit(main())
