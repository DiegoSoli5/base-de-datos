import asyncio
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

from bson import json_util
from playwright.async_api import async_playwright
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

CARPETA = Path(__file__).resolve().parent
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(CARPETA / ".browsers")
MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "pinterest_tattoos_db"
COLLECTION_NAME = "skull_tattoos"
BUSQUEDAS = [
    "tatuajes calaveras de azucar",
    "tatuajes calaveras realistas",
    "tatuaje calavera con rosas",
    "skull tattoo design blackwork",
]


async def scrape_skull_tattoos(context, collection, search_query, max_results=10):
    """Completa diez documentos por búsqueda, sin repetir imágenes."""
    cantidad = collection.count_documents({"search_term": search_query})
    if cantidad >= max_results:
        print(f"{search_query}: {cantidad} registros existentes.")
        return

    page = await context.new_page()
    try:
        url = f"https://www.pinterest.com/search/pins/?q={quote(search_query)}"
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(4000)
        for _ in range(10):
            imagenes = await page.locator('img[src*="i.pinimg.com"]').evaluate_all(
                "imgs => imgs.map(img => ({src: img.src, alt: img.alt}))"
            )
            for img in imagenes:
                if cantidad >= max_results:
                    break
                src = img["src"]
                if not re.search(r"/(236x|474x|736x)/", src):
                    continue
                original = re.sub(r"/(236x|474x|736x)/", "/originals/", src)
                if collection.find_one({"image_url": {"$in": [original, src]}}):
                    continue
                # Algunas imágenes no tienen versión /originals/: usar la real.
                respuesta = await context.request.get(original, timeout=30000)
                valida = respuesta.ok and respuesta.headers.get("content-type", "").startswith("image/")
                await respuesta.dispose()
                image_url = original if valida else src
                titulo = img["alt"]
                if not titulo or titulo.lower() in {"pin", "image"}:
                    titulo = search_query
                tags = {t.lower() for t in re.findall(r"\b\w+\b", titulo) if len(t) > 3}
                tags.update(["calavera", "tattoo", search_query.lower()])
                documento = {
                    "title": titulo,
                    "category": "Skull Tattoos",
                    "search_term": search_query,
                    "image_url": image_url,
                    "thumbnail_url": src,
                    "tags": sorted(tags),
                    "source": "Pinterest",
                    "created_at": datetime.now(timezone.utc),
                }
                try:
                    collection.insert_one(documento)
                    cantidad += 1
                    print(f"[{cantidad}/{max_results}] {search_query}", flush=True)
                except DuplicateKeyError:
                    pass
            if cantidad >= max_results:
                break
            await page.evaluate("window.scrollBy(0, 1200)")
            await page.wait_for_timeout(2000)
        if cantidad < max_results:
            raise RuntimeError(f"Pinterest solo permitió obtener {cantidad}/{max_results}: {search_query}")
    finally:
        await page.close()


async def main():
    with MongoClient(MONGO_URI, serverSelectionTimeoutMS=60000) as client:
        client.admin.command("ping")
        collection = client[DB_NAME][COLLECTION_NAME]
        collection.create_index("image_url", unique=True)
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            try:
                context = await browser.new_context(viewport={"width": 1280, "height": 800})
                for busqueda in BUSQUEDAS:
                    await scrape_skull_tattoos(context, collection, busqueda)
            finally:
                await browser.close()
        total = collection.count_documents({})
        if total != 40:
            raise RuntimeError(f"Se esperaban 40 documentos, hay {total}.")
        (CARPETA / "tatuajes.json").write_text(
            json_util.dumps(list(collection.find()), indent=2, ensure_ascii=False), encoding="utf-8"
        )
        print(f"Verificado: {total} documentos en {DB_NAME}.{COLLECTION_NAME}.")


if __name__ == "__main__":
    asyncio.run(main())
