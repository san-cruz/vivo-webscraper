"""
scrapertxt.py — Scraper Vivo → arquivos .txt
---------------------------------------------
Lê as páginas de ativacao-servicos-digitais/* via Playwright,
extrai o bloco #main-content e salva um .txt estruturado por página.

Uso:
    python scrapertxt.py                     # processa todas as páginas
    python scrapertxt.py ativacao-spotify    # processa apenas um slug
    python scrapertxt.py --list              # lista todos os slugs disponíveis

Saída:
    output/txt/<slug>.txt
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from extractor import (
    ACTIVATION_PAGES,
    build_url,
    fetch_main_content,
    extract_meta,
    extract_sections,
)

OUTPUT_DIR = Path(__file__).parent / "output" / "txt"


# ──────────────────────────────────────────────
# Gerador de .txt
# ──────────────────────────────────────────────

def save_txt(slug: str, meta: dict, sections: list[dict]) -> Path:
    """
    Gera o .txt no formato padrão Vivo:

      SEÇÃO: <título da página>

      <Subtítulo>

      Passos:
      1. -item

      Subtítulo FAQ:
      1. Pergunta?
      Resposta.

      - item de lista
    """
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = OUTPUT_DIR / f"{slug}.txt"

    with open(path, "w", encoding="utf-8") as f:
        page_title = meta["title"] or slug
        f.write(f"SEÇÃO: {page_title}\n")
        if meta.get("description"):
            f.write(f"\n{meta['description']}\n")
        f.write("\n")

        for section in sections:
            if section["title"]:
                f.write(f"\n{section['title']}\n")

            for block in section["blocks"]:
                if block["type"] == "paragraph":
                    f.write(f"{block['text']}\n")

                elif block["type"] == "heading":
                    f.write(f"\n{block['text']}\n")

                elif block["type"] == "ordered":
                    f.write("Passos:\n")
                    for i, item in enumerate(block["items"], 1):
                        f.write(f"{i}. -{item}\n")
                    f.write("\n")

                elif block["type"] == "unordered":
                    for item in block["items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")

                elif block["type"] == "faq":
                    for i, faq in enumerate(block["items"], 1):
                        f.write(f"{i}. {faq['q']}\n")
                        if faq["a"]:
                            f.write(f"{faq['a']}\n")
                    f.write("\n")

            f.write("\n")

    return path


# ──────────────────────────────────────────────
# Pipeline
# ──────────────────────────────────────────────

async def process_page(page, slug: str) -> None:
    url = build_url(slug)
    print(f"\n🌐 [{slug}]  {url}")

    soup = await fetch_main_content(page, url)
    if soup is None:
        print("   ❌ Não foi possível obter o conteúdo.")
        return

    meta = extract_meta(soup)
    sections = extract_sections(soup)

    txt_path = save_txt(slug, meta, sections)

    print(f"   ✅ Título   : {meta['title'] or '(sem título)'}")
    print(f"   📑 Seções  : {len(sections)}")
    print(f"   💾 Arquivo : {txt_path.relative_to(Path(__file__).parent)}")


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapertxt.py — {len(slugs)} página(s) para processar\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        )
        pg = await context.new_page()

        for slug in slugs:
            try:
                await process_page(pg, slug)
            except Exception as e:
                print(f"   ❌ Erro em [{slug}]: {e}")

        await browser.close()

    print(f"\n🎉 Concluído! TXTs salvos em: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list" in args:
        print("Slugs disponíveis:")
        for s in ACTIVATION_PAGES:
            print(f"  {s}  →  {build_url(s)}")
        sys.exit(0)

    # Filtra slugs válidos passados como argumento, ou usa todos
    if args:
        invalid = [a for a in args if a not in ACTIVATION_PAGES]
        if invalid:
            print(f"⚠️  Slugs inválidos: {', '.join(invalid)}")
            print(f"   Use --list para ver os disponíveis.")
            sys.exit(1)
        slugs_to_run = args
    else:
        slugs_to_run = ACTIVATION_PAGES

    asyncio.run(main(slugs_to_run))