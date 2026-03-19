"""
scrapertxt.py — Scraper Vivo → arquivos .txt

Uso:
  python scrapertxt.py                          # todas as páginas
  python scrapertxt.py ativacao-spotify         # slug específico
  python scrapertxt.py --category "Fatura"      # categoria inteira
  python scrapertxt.py --list                   # lista slugs e URLs
"""

import asyncio, sys, re, inspect
from pathlib import Path
from playwright.async_api import async_playwright
from extractors import get_extractor
from extractors.base import build_url, get_all_slugs, get_slugs_by_category, get_categories, get_entry, fetch_main_content, extract_meta

OUTPUT_DIR = Path(__file__).parent / "output" / "outputs-txt"


def _category_to_folder(category: str) -> str:
    s = category.lower()
    s = re.sub(r"[—–]", "-", s)
    s = s.translate(str.maketrans("ãâáàêéèíîõôóúûç ", "aaaaeeeiiooouuc-"))
    s = re.sub(r"[^a-z0-9-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")


def save_txt(slug: str, meta: dict, sections: list[dict]) -> Path:
    entry = get_entry(slug)
    folder = OUTPUT_DIR / _category_to_folder(entry["category"])
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{slug}.txt"
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"SEÇÃO: {meta['title'] or slug}\n")
        if meta.get("description"): f.write(f"\n{meta['description']}\n")
        f.write("\n")
        for section in sections:
            if section["title"]: f.write(f"\n{section['title']}\n")
            for block in section["blocks"]:
                t = block["type"]
                if t == "paragraph": f.write(f"{block['text']}\n")
                elif t == "heading": f.write(f"\n{block['text']}\n")
                elif t == "blank": f.write("\n")
                elif t == "ordered":
                    f.write("Passos:\n")
                    for i, item in enumerate(block["items"], 1): f.write(f"{i}. -{item}\n")
                    f.write("\n")
                elif t == "unordered":
                    for item in block["items"]: f.write(f"- {item}\n")
                    f.write("\n")
                elif t == "faq":
                    for i, faq in enumerate(block["items"], 1):
                        f.write(f"{i}. {faq['q']}\n")
                        if faq["a"]: f.write(f"{faq['a']}\n")
                    f.write("\n")
            f.write("\n")
    return path


async def process_page(page, slug: str) -> bool:
    url = build_url(slug)
    entry = get_entry(slug)
    print(f"\n🌐 [{slug}]\n   URL      : {url}\n   Categoria: {entry['category']}")
    try:
        extractor = get_extractor(slug)
    except NotImplementedError as e:
        print(f"   ⏭️  Pulado: {e}"); return False
    soup = await fetch_main_content(page, url)
    if soup is None:
        print("   ❌ Não foi possível obter o conteúdo."); return False
    meta = extract_meta(soup)
    sig = inspect.signature(extractor.extract_sections)
    sections = extractor.extract_sections(soup, page_url=url) if "page_url" in sig.parameters else extractor.extract_sections(soup)
    txt_path = save_txt(slug, meta, sections)
    print(f"   ✅ Título  : {meta['title'] or '(sem título)'}\n   📑 Seções : {len(sections)}\n   💾 Arquivo: {txt_path.relative_to(Path(__file__).parent)}")
    return True


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapertxt.py — {len(slugs)} página(s) para processar\n   Saída: {OUTPUT_DIR.resolve()}\n")
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(locale="pt-BR", user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
        pg = await context.new_page()
        ok = fail = 0
        for i, slug in enumerate(slugs, 1):
            print(f"── [{i}/{len(slugs)}] ─────────────────────────────")
            try:
                ok += await process_page(pg, slug)
            except Exception as e:
                print(f"   ❌ Erro inesperado em [{slug}]: {e}"); fail += 1
        await browser.close()
    print(f"\n{'═'*50}\n🎉 Concluído!  ✅ {ok} ok   ❌ {fail} falhas   📄 {len(slugs)} total\n   TXTs salvos em: {OUTPUT_DIR.resolve()}")


def parse_args(argv: list[str]) -> tuple[list[str], bool]:
    show_list = "--list" in argv
    argv_clean = [a for a in argv if a != "--list"]
    category_filter = None
    if "--category" in argv_clean:
        idx = argv_clean.index("--category")
        if idx + 1 < len(argv_clean):
            category_filter = argv_clean[idx + 1]
            argv_clean = argv_clean[:idx] + argv_clean[idx + 2:]
        else:
            print("⚠️  --category requer um argumento."); sys.exit(1)
    positional = [a for a in argv_clean if not a.startswith("--")]
    all_slugs = get_all_slugs()
    if positional:
        invalid = [s for s in positional if s not in all_slugs]
        if invalid:
            print(f"⚠️  Slugs inválidos: {', '.join(invalid)}\n   Use --list para ver os disponíveis."); sys.exit(1)
        slugs = positional
    elif category_filter:
        slugs = get_slugs_by_category(category_filter)
        if not slugs:
            print(f"⚠️  Nenhuma página para '{category_filter}'.\n   Categorias: {', '.join(get_categories())}"); sys.exit(1)
    else:
        slugs = all_slugs
    return slugs, show_list


def print_list(slugs: list[str]) -> None:
    current_cat = None
    for slug in slugs:
        entry = get_entry(slug)
        if entry["category"] != current_cat:
            current_cat = entry["category"]
            print(f"\n  📂 {current_cat}\n  {'─'*50}")
        print(f"  {slug:<40} → {build_url(slug)}")


if __name__ == "__main__":
    slugs_to_run, show_list = parse_args(sys.argv[1:])
    if show_list:
        print(f"\n📋 Catálogo de páginas válidas para TXT ({len(slugs_to_run)} páginas)\n")
        print_list(slugs_to_run)
        print(f"\n  Total: {len(slugs_to_run)} páginas em {len(get_categories())} categorias\n")
        sys.exit(0)
    asyncio.run(main(slugs_to_run))