"""
scrapercsv.py — Scraper Vivo → arquivos .csv

Uso:
  python scrapercsv.py                     # processa todas as páginas de ativação
  python scrapercsv.py ativacao-spotify    # processa apenas um slug
  python scrapercsv.py --list              # lista todos os slugs de ativação
"""

import asyncio, csv, sys
from pathlib import Path
from playwright.async_api import async_playwright
from extractor import ACTIVATION_PAGES, build_url, get_all_slugs, fetch_main_content, extract_meta, extract_sections, extract_links, extract_tables, flatten_text_blocks

OUTPUT_DIR = Path(__file__).parent / "output" / "outputs-csv"


def save_csv_links(slug, links): return _save_csv(slug, "_links.csv", ["text","href"], links)
def save_csv_texts(slug, text_blocks):
    path = OUTPUT_DIR / f"{slug}_textos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["#","texto"])
        for i, b in enumerate(text_blocks, 1): w.writerow([i, b])
    return path
def save_csv_table(slug, table_index, rows):
    path = OUTPUT_DIR / f"{slug}_tabela{table_index}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f: csv.writer(f).writerows(rows)
    return path

def _save_csv(slug, suffix, fieldnames, rows):
    path = OUTPUT_DIR / f"{slug}{suffix}"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader(); w.writerows(rows)
    return path


async def process_page(page, slug: str) -> None:
    url = build_url(slug)
    print(f"\n🌐 [{slug}]  {url}")
    soup = await fetch_main_content(page, url)
    if soup is None: print("   ❌ Não foi possível obter o conteúdo."); return
    meta = extract_meta(soup)
    sections = extract_sections(soup)
    links, tables = extract_links(soup), extract_tables(soup)
    text_blocks = flatten_text_blocks(sections)
    generated = [*([ save_csv_links(slug, links)] if links else []), save_csv_texts(slug, text_blocks), *[save_csv_table(slug, i, rows) for i, rows in enumerate(tables, 1)]]
    print(f"   ✅ Título  : {meta['title'] or '(sem título)'}\n   🔗 Links  : {len(links)}\n   📝 Blocos : {len(text_blocks)}\n   📊 Tabelas: {len(tables)}\n   💾 Arquivos:")
    for p in generated: print(f"      → {p.relative_to(Path(__file__).parent)}")


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapercsv.py — {len(slugs)} página(s) para processar\n")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(locale="pt-BR", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        pg = await context.new_page()
        for slug in slugs:
            try: await process_page(pg, slug)
            except Exception as e: print(f"   ❌ Erro em [{slug}]: {e}")
        await browser.close()
    print(f"\n🎉 Concluído! CSVs salvos em: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    args = sys.argv[1:]
    if "--list" in args:
        print("Slugs disponíveis (páginas de ativação):")
        for s in ACTIVATION_PAGES: print(f"  {s}  →  {build_url(s)}")
        sys.exit(0)
    if args:
        invalid = [a for a in args if a not in get_all_slugs()]
        if invalid: print(f"⚠️  Slugs inválidos: {', '.join(invalid)}\n   Use --list para ver os disponíveis."); sys.exit(1)
        slugs_to_run = args
    else:
        slugs_to_run = ACTIVATION_PAGES
    asyncio.run(main(slugs_to_run))