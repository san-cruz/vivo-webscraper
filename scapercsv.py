"""
scrapercsv.py — Scraper Vivo → arquivos .csv
---------------------------------------------
Lê as páginas de ativacao-servicos-digitais/* via Playwright,
extrai o bloco #main-content e salva CSVs por página.

Arquivos gerados por slug:
  output/csv/<slug>_links.csv      → todos os links (texto + href)
  output/csv/<slug>_textos.csv     → blocos de texto extraídos
  output/csv/<slug>_tabelaN.csv    → tabelas HTML (se existirem)

Uso:
    python scrapercsv.py                     # processa todas as páginas
    python scrapercsv.py ativacao-spotify    # processa apenas um slug
    python scrapercsv.py --list              # lista todos os slugs disponíveis
"""

import asyncio
import csv
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from extractor import (
    ACTIVATION_PAGES,
    build_url,
    fetch_main_content,
    extract_meta,
    extract_sections,
    extract_links,
    extract_tables,
    flatten_text_blocks,
)

OUTPUT_DIR = Path(__file__).parent / "output" / "csv"


# ──────────────────────────────────────────────
# Geradores de CSV
# ──────────────────────────────────────────────

def save_csv_links(slug: str, links: list[dict]) -> Path:
    path = OUTPUT_DIR / f"{slug}_links.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "href"])
        writer.writeheader()
        writer.writerows(links)
    return path


def save_csv_texts(slug: str, text_blocks: list[str]) -> Path:
    path = OUTPUT_DIR / f"{slug}_textos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "texto"])
        for i, block in enumerate(text_blocks, 1):
            writer.writerow([i, block])
    return path


def save_csv_table(slug: str, table_index: int, rows: list[list[str]]) -> Path:
    path = OUTPUT_DIR / f"{slug}_tabela{table_index}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
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
    links = extract_links(soup)
    tables = extract_tables(soup)
    text_blocks = flatten_text_blocks(sections)

    generated = []

    if links:
        generated.append(save_csv_links(slug, links))

    generated.append(save_csv_texts(slug, text_blocks))

    for i, table_rows in enumerate(tables, 1):
        generated.append(save_csv_table(slug, i, table_rows))

    print(f"   ✅ Título  : {meta['title'] or '(sem título)'}")
    print(f"   🔗 Links  : {len(links)}")
    print(f"   📝 Blocos : {len(text_blocks)}")
    print(f"   📊 Tabelas: {len(tables)}")
    print(f"   💾 Arquivos:")
    for p in generated:
        print(f"      → {p.relative_to(Path(__file__).parent)}")


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapercsv.py — {len(slugs)} página(s) para processar\n")

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

    print(f"\n🎉 Concluído! CSVs salvos em: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    args = sys.argv[1:]

    if "--list" in args:
        print("Slugs disponíveis:")
        for s in ACTIVATION_PAGES:
            print(f"  {s}  →  {build_url(s)}")
        sys.exit(0)

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