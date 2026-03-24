"""
scrapertxt-faq.py — Scraper Vivo → arquivos .txt somente com FAQ

Extrai apenas os blocos de FAQ de cada página.
Se a página não tiver FAQ, registra aviso no console e não gera arquivo.

Uso:
  python scrapertxt-faq.py                          # todas as páginas
  python scrapertxt-faq.py duvidas-internet-wifi     # slug específico
  python scrapertxt-faq.py --category "Fatura"       # categoria inteira
  python scrapertxt-faq.py --list                    # lista slugs e URLs
"""

import asyncio, sys, re, inspect
from pathlib import Path
from playwright.async_api import async_playwright
from extractors import get_extractor
from extractors.base import build_url, get_all_slugs, get_slugs_by_category, get_categories, get_entry, fetch_main_content, extract_meta

# Mesmo diretório base do scrapertxt.py
OUTPUT_DIR = Path(__file__).parent / "output" / "outputs-txt-faqs"


def _category_to_folder(category: str) -> str:
    s = category.lower()
    s = re.sub(r"[—–]", "-", s)
    s = s.translate(str.maketrans("ãâáàêéèíîõôóúûç ", "aaaaeeeiiooouuc-"))
    s = re.sub(r"[^a-z0-9-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")



# Títulos de itens de acordeão que não são FAQ real — são blocos legais/informativos
# que o componente faq-container-component da Vivo agrupa junto com o FAQ.
_NON_FAQ_TITLES: tuple[str, ...] = (
    "informações gerais",
    "informações adicionais",
    "preços e tarifas",
    "preço e tarifa",
    "termos e condições",
    "regulamento",
    "notas",
    "Vale Bonus",
    "vale bônus",
    "grade de canais",
)


def _is_non_faq_item(question: str) -> bool:
    """Retorna True se o item do acordeão for um bloco legal/informativo, não FAQ real."""
    q_lower = question.lower().strip()
    return any(q_lower.startswith(title) for title in _NON_FAQ_TITLES)


def _collect_faq_blocks(sections: list[dict]) -> list[dict]:
    """Extrai todos os blocos do tipo 'faq' de todas as seções,
    filtrando itens que são blocos legais/informativos e não perguntas reais."""
    faq_blocks = []
    for section in sections:
        for block in section.get("blocks", []):
            if block["type"] == "faq" and block.get("items"):
                filtered_items = [
                    item for item in block["items"]
                    if not _is_non_faq_item(item["q"])
                ]
                if filtered_items:
                    faq_blocks.append({
                        "section_title": section.get("title", ""),
                        "items": filtered_items,
                    })
    return faq_blocks


def save_faq_txt(slug: str, meta: dict, faq_blocks: list[dict]) -> Path:
    entry = get_entry(slug)
    folder = OUTPUT_DIR / _category_to_folder(entry["category"])
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{slug}-faq.txt"

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"SEÇÃO: {meta['title'] or slug}\n\n")

        for faq_block in faq_blocks:
            if faq_block["section_title"]:
                f.write(f"{faq_block['section_title']}\n")

            for index, faq in enumerate(faq_block["items"], 1):
                f.write(f"{index}. {faq['q']}\n")
                if faq["a"]:
                    f.write(f"{faq['a']}\n")

            f.write("\n")

    return path


async def process_page(page, slug: str) -> bool:
    url = build_url(slug)
    entry = get_entry(slug)
    print(f"\n🌐 [{slug}]\n   URL      : {url}\n   Categoria: {entry['category']}")

    try:
        extractor = get_extractor(slug)
    except NotImplementedError as e:
        print(f"   ⏭️  Pulado: {e}")
        return False

    soup = await fetch_main_content(page, url)
    if soup is None:
        print("   ❌ Não foi possível obter o conteúdo.")
        return False

    meta = extract_meta(soup)
    sig = inspect.signature(extractor.extract_sections)
    sections = (
        extractor.extract_sections(soup, page_url=url)
        if "page_url" in sig.parameters
        else extractor.extract_sections(soup)
    )

    faq_blocks = _collect_faq_blocks(sections)

    if not faq_blocks:
        print(f"   ⚠️  Nenhum FAQ encontrado nesta página.")
        return False

    total_faqs = sum(len(b["items"]) for b in faq_blocks)
    txt_path = save_faq_txt(slug, meta, faq_blocks)
    print(
        f"   ✅ Título  : {meta['title'] or '(sem título)'}\n"
        f"   ❓ FAQs    : {total_faqs} pergunta(s)\n"
        f"   💾 Arquivo: {txt_path.relative_to(Path(__file__).parent)}"
    )
    return True


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapertxt-faq.py — {len(slugs)} página(s) para processar\n   Saída: {OUTPUT_DIR.resolve()}\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        context = await browser.new_context(
            locale="pt-BR",
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            ),
        )
        pg = await context.new_page()
        ok = fail = no_faq = 0

        for i, slug in enumerate(slugs, 1):
            print(f"── [{i}/{len(slugs)}] ─────────────────────────────")
            try:
                result = await process_page(pg, slug)
                if result:
                    ok += 1
                else:
                    no_faq += 1
            except Exception as e:
                print(f"   ❌ Erro inesperado em [{slug}]: {e}")
                fail += 1

        await browser.close()

    print(
        f"\n{'═'*50}\n"
        f"🎉 Concluído!\n"
        f"   ✅ {ok} com FAQ salvo\n"
        f"   ⚠️  {no_faq} sem FAQ\n"
        f"   ❌ {fail} falhas\n"
        f"   📄 {len(slugs)} total\n"
        f"   TXTs salvos em: {OUTPUT_DIR.resolve()}"
    )


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
            print("⚠️  --category requer um argumento.")
            sys.exit(1)

    positional = [a for a in argv_clean if not a.startswith("--")]
    all_slugs = get_all_slugs()

    if positional:
        invalid = [s for s in positional if s not in all_slugs]
        if invalid:
            print(f"⚠️  Slugs inválidos: {', '.join(invalid)}\n   Use --list para ver os disponíveis.")
            sys.exit(1)
        slugs = positional
    elif category_filter:
        slugs = get_slugs_by_category(category_filter)
        if not slugs:
            print(f"⚠️  Nenhuma página para '{category_filter}'.\n   Categorias: {', '.join(get_categories())}")
            sys.exit(1)
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
        print(f"\n📋 Catálogo de páginas válidas para FAQ ({len(slugs_to_run)} páginas)\n")
        print_list(slugs_to_run)
        print(f"\n  Total: {len(slugs_to_run)} páginas em {len(get_categories())} categorias\n")
        sys.exit(0)
    asyncio.run(main(slugs_to_run))