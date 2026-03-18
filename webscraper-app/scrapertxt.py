"""
scrapertxt.py — Scraper Vivo → arquivos .txt
---------------------------------------------
Lê as páginas informativas do site Vivo via Playwright,
extrai o bloco #main-content e salva um .txt estruturado por página.

Páginas suportadas: 47 URLs válidas distribuídas em 8 categorias.
Regra de inclusão: apenas páginas estáticas e informativas —
sem seções de valores de produtos, pacotes ou planos comerciais.

─────────────────────────────────────────────────────────────────
USO
─────────────────────────────────────────────────────────────────
  python scrapertxt.py                          # todas as páginas
  python scrapertxt.py ativacao-spotify         # slug específico
  python scrapertxt.py slug-a slug-b slug-c     # múltiplos slugs
  python scrapertxt.py --category "Fatura"      # categoria inteira
  python scrapertxt.py --list                   # lista slugs e URLs
  python scrapertxt.py --list --category "Dúvidas — Internet"

─────────────────────────────────────────────────────────────────
SAÍDA
─────────────────────────────────────────────────────────────────
  output/txt/<categoria>/<slug>.txt     — um arquivo por página
"""

import asyncio
import sys
from pathlib import Path

from playwright.async_api import async_playwright

from extractors import get_extractor
from extractors.base import (
    build_url,
    get_all_slugs,
    get_slugs_by_category,
    get_categories,
    get_entry,
    fetch_main_content,
    extract_meta,
)

import re

OUTPUT_DIR = Path(__file__).parent / "output" / "outputs-txt"


def _category_to_folder(category: str) -> str:
    """Converte nome de categoria em slug de pasta (ex: 'Dúvidas — TV' → 'duvidas-tv')."""
    s = category.lower()
    s = re.sub(r"[—–]", "-", s)
    s = s.translate(str.maketrans(
        "ãâáàêéèíîõôóúûç ",
        "aaaaeeeiiooouuc-"
    ))
    s = re.sub(r"[^a-z0-9-]", "", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


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
    entry = get_entry(slug)
    folder = OUTPUT_DIR / _category_to_folder(entry["category"])
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{slug}.txt"

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
                    # Parágrafos com \n embutido (ex: cards "Título\nLink: url")
                    # são escritos em múltiplas linhas preservando a quebra.
                    f.write(f"{block['text']}\n")

                elif block["type"] == "heading":
                    f.write(f"\n{block['text']}\n")

                elif block["type"] == "blank":
                    # Separador entre grupos de conteúdo (ex: cards de carrossel)
                    f.write("\n")

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

async def process_page(page, slug: str) -> bool:
    """Processa uma única página. Retorna True em caso de sucesso."""
    url = build_url(slug)
    entry = get_entry(slug)
    print(f"\n🌐 [{slug}]")
    print(f"   URL      : {url}")
    print(f"   Categoria: {entry['category']}")

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
    # Passa a URL da página para extractors que precisam resolver âncoras relativas
    # (ex: ajuda-e-autoatendimento — acesso-rapido com hrefs "#secao")
    import inspect
    sig = inspect.signature(extractor.extract_sections)
    if "page_url" in sig.parameters:
        sections = extractor.extract_sections(soup, page_url=url)
    else:
        sections = extractor.extract_sections(soup)
    txt_path = save_txt(slug, meta, sections)

    print(f"   ✅ Título  : {meta['title'] or '(sem título)'}")
    print(f"   📑 Seções : {len(sections)}")
    print(f"   💾 Arquivo: {txt_path.relative_to(Path(__file__).parent)}")
    return True


async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    total = len(slugs)
    print(f"🚀 scrapertxt.py — {total} página(s) para processar")
    print(f"   Saída: {OUTPUT_DIR.resolve()}\n")

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

        ok = 0
        fail = 0
        for i, slug in enumerate(slugs, 1):
            print(f"── [{i}/{total}] ─────────────────────────────")
            try:
                success = await process_page(pg, slug)
                if success:
                    ok += 1
                else:
                    fail += 1
            except Exception as e:
                print(f"   ❌ Erro inesperado em [{slug}]: {e}")
                fail += 1

        await browser.close()

    print(f"\n{'═' * 50}")
    print(f"🎉 Concluído!  ✅ {ok} ok   ❌ {fail} falhas   📄 {total} total")
    print(f"   TXTs salvos em: {OUTPUT_DIR.resolve()}")


# ──────────────────────────────────────────────
# Parsing de argumentos
# ──────────────────────────────────────────────

def parse_args(argv: list[str]) -> tuple[list[str], bool]:
    """
    Retorna (slugs_para_processar, show_list).
    Flags suportadas:
      --list               imprime catálogo e sai
      --category <nome>    filtra por categoria (case-insensitive, substring)
    Argumentos posicionais são tratados como slugs.
    """
    show_list = "--list" in argv
    argv_clean = [a for a in argv if a != "--list"]

    # Extrai --category <valor>
    category_filter: str | None = None
    if "--category" in argv_clean:
        idx = argv_clean.index("--category")
        if idx + 1 < len(argv_clean):
            category_filter = argv_clean[idx + 1]
            argv_clean = argv_clean[:idx] + argv_clean[idx + 2:]
        else:
            print("⚠️  --category requer um argumento. Exemplo: --category \"Fatura\"")
            sys.exit(1)

    # Slugs posicionais
    positional = [a for a in argv_clean if not a.startswith("--")]

    all_slugs = get_all_slugs()

    if positional:
        invalid = [s for s in positional if s not in all_slugs]
        if invalid:
            print(f"⚠️  Slugs inválidos: {', '.join(invalid)}")
            print("   Use --list para ver os disponíveis.")
            sys.exit(1)
        slugs = positional
    elif category_filter:
        slugs = get_slugs_by_category(category_filter)
        if not slugs:
            print(f"⚠️  Nenhuma página encontrada para a categoria '{category_filter}'.")
            print(f"   Categorias disponíveis: {', '.join(get_categories())}")
            sys.exit(1)
    else:
        slugs = all_slugs

    return slugs, show_list


def print_list(slugs: list[str]) -> None:
    """Imprime o catálogo de páginas agrupado por categoria."""
    current_cat = None
    for slug in slugs:
        entry = get_entry(slug)
        if entry["category"] != current_cat:
            current_cat = entry["category"]
            print(f"\n  📂 {current_cat}")
            print(f"  {'─' * 50}")
        url = build_url(slug)
        print(f"  {slug:<40} → {url}")


if __name__ == "__main__":
    args = sys.argv[1:]
    slugs_to_run, show_list = parse_args(args)

    if show_list:
        total = len(slugs_to_run)
        print(f"\n📋 Catálogo de páginas válidas para TXT ({total} páginas)\n")
        print_list(slugs_to_run)
        print(f"\n  Total: {total} páginas em {len(get_categories())} categorias\n")
        sys.exit(0)

    asyncio.run(main(slugs_to_run))