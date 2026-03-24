"""
scrapertxt-structured.py — Scraper Vivo → arquivos .txt com formato estruturado

Gera arquivos .txt seguindo a estrutura do canais-adicionais-ref.txt:
  - Cabeçalho com título da página e descrição
  - Seção COMO CONTRATAR (side-by-side-component)
  - Seções por categoria (h2 + p.body)
  - Itens de canal/produto extraídos dos destaque-banner
    com campos: Nome, Descrição, Preço e Link
  - Seção Adultos com aviso de conteúdo restrito
  - Rodapé com nota de atenção (legaltext)

Uso:
  python scrapertxt-structured.py                         # todas as páginas do catálogo
  python scrapertxt-structured.py canais-adicionais       # slug específico
  python scrapertxt-structured.py --category "Conteúdos Complementares"
  python scrapertxt-structured.py --list                  # lista slugs e URLs
"""

import asyncio
import re
import sys
from pathlib import Path

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright

# ── Importa utilitários do projeto ─────────────────────────────────────────
from extractors.base import (
    BASE_URL,
    PAGE_CATALOG,
    _normalize_href,
    build_url,
    clean_text,
    fetch_main_content,
    extract_meta,
    get_all_slugs,
    get_categories,
    get_entry,
    get_slugs_by_category,
)

OUTPUT_DIR = Path(__file__).parent / "output" / "outputs-txt-structured"

SEP_FULL  = "=" * 80
SEP_HALF  = "-" * 80


# ──────────────────────────────────────────────────────────────────────────────
# Helpers de extração específicos para o formato estruturado
# ──────────────────────────────────────────────────────────────────────────────

def _extract_side_by_side_bullets(container: Tag) -> list[str]:
    """
    Extrai os itens do side-by-side-component como bullet list simples
    (texto das divs card-text__content, sem links de imagem).
    """
    items = []
    for card in container.find_all("div", class_="card-text"):
        content = card.find("div", class_="card-text__content")
        if content:
            text = clean_text(content.get_text())
            if text:
                items.append(text)
    return items


def _extract_destaque_banner_channels(banner_div: Tag) -> list[dict]:
    """
    Extrai lista de canais/produtos de um .destaque-banner.

    Cada item retorna:
      name        → p.overline
      description → h2.h3 / h3.h3
      price       → span.h4 (sem o SVG)
      href        → a[href] do item (None se for modal/adulto)
      is_modal    → True quando o link aponta para um modal (canais adultos)
    """
    channels = []
    for item in banner_div.find_all("div", class_="destaque-banner__item"):
        content = item.find("div", class_="destaque-banner__item__content")
        if not content:
            continue

        name_tag  = content.find("p", class_="overline")
        desc_tag  = content.find("h2") or content.find("h3")
        price_tag = content.find("span", class_="h4")

        name  = clean_text(name_tag.get_text())  if name_tag  else ""
        desc  = clean_text(desc_tag.get_text())  if desc_tag  else ""

        # Remove o SVG do preço antes de pegar o texto
        price = ""
        if price_tag:
            for svg in price_tag.find_all("svg"):
                svg.decompose()
            price = clean_text(price_tag.get_text())

        # Link: tenta href direto; detecta modal pelo data-target
        link_tag = item.find("a", class_="banner__link")
        href     = None
        is_modal = False
        if link_tag:
            raw = link_tag.get("href", "").strip()
            if raw and not raw.startswith("#"):
                href = _normalize_href(raw)
            elif link_tag.get("data-target"):          # canais adultos usam modal
                is_modal = True

        if name or desc:
            channels.append({
                "name":     name,
                "description": desc,
                "price":    price,
                "href":     href,
                "is_modal": is_modal,
            })
    return channels


def _extract_adult_modal_link(soup: BeautifulSoup) -> str | None:
    """
    Extrai o link 'Quero acessar' do modal de conteúdo adulto.
    Retorna a URL normalizada ou None.
    """
    for a in soup.find_all("a", class_="btn-purple"):
        href = a.get("href", "").strip()
        if href and not href.startswith("#"):
            return _normalize_href(href)
    return None


def _extract_legaltext(soup: BeautifulSoup) -> list[str]:
    """Extrai parágrafos do legaltext-component (rodapé de atenção)."""
    lines = []
    for lt in soup.find_all("div", class_="legaltext-component"):
        for p in lt.find_all("p"):
            # Ignora parágrafos que só contenham links âncora (#)
            text = clean_text(p.get_text())
            if text and text not in lines:
                lines.append(text)
    return lines


# ──────────────────────────────────────────────────────────────────────────────
# Estrutura principal de extração da página
# ──────────────────────────────────────────────────────────────────────────────

def extract_structured_sections(soup: BeautifulSoup) -> dict:
    """
    Extrai todas as seções relevantes da página no modelo estruturado.

    Retorna um dict com:
      page_title   : str
      description  : str   (meta description)
      intro        : str   (p do comunicados, abaixo do h1)
      how_to_hire  : list[str]   (bullets do side-by-side-component)
      categories   : list[dict] com keys:
                       title    : str
                       subtitle : str   (p.body logo abaixo do h2)
                       channels : list[dict]  (name, description, price, href, is_modal)
                       is_adult : bool
      adult_modal_link : str | None
      legaltext    : list[str]
    """
    result = {
        "page_title":       "",
        "description":      "",
        "intro":            "",
        "how_to_hire":      [],
        "categories":       [],
        "adult_modal_link": None,
        "legaltext":        [],
    }

    # ── Título h1 ──────────────────────────────────────────────────────────
    h1 = soup.find("h1")
    if h1:
        result["page_title"] = clean_text(h1.get_text())

    # ── Intro (primeiro comunicados) ───────────────────────────────────────
    first_comunicados = soup.find("div", class_="comunicados")
    if first_comunicados:
        p = first_comunicados.find("p")
        if p:
            result["intro"] = clean_text(p.get_text())

    # ── Como contratar (side-by-side-component) ────────────────────────────
    sbs = soup.find("div", class_="side-by-side-component")
    if sbs:
        result["how_to_hire"] = _extract_side_by_side_bullets(sbs)

    # ── Categorias: percorre h2 + destaque-banner em ordem DOM ────────────
    # Mapeamos cada h2 a todos os destaque-banner que aparecem antes do
    # próximo h2 (ou fim de página).

    # Coleta todos os h2 e todos os destaque-banner em ordem de aparecimento
    # usando posição no DOM (comparação de source_line ou iteração flat).

    body = soup.body or soup
    current_category: dict | None = None
    adult_categories_anchors: set[str] = {"adultos"}  # âncoras DOM que indicam adulto

    # Detecta se estamos dentro de uma seção adulta através da âncora anterior
    last_anchor_id: str = ""

    def _is_adult_section() -> bool:
        return last_anchor_id in adult_categories_anchors

    def _flush_category():
        if current_category and (current_category["title"] or current_category["channels"]):
            result["categories"].append(current_category)

    def walk_for_categories(node: Tag) -> None:
        nonlocal current_category, last_anchor_id

        if not isinstance(node, Tag):
            return

        classes = node.get("class", [])

        # ── Âncora de seção ─────────────────────────────────────────────
        anchor_div = node.find("div", attrs={"data-controller": "anchor"}) if node.name == "div" else None
        if anchor_div and anchor_div.get("data-anchor"):
            last_anchor_id = anchor_div.get("data-anchor", "")

        # ── Título de categoria (h2 dentro de div.title) ─────────────────
        if "title" in classes and node.name == "div":
            h2 = node.find("h2")
            if h2:
                _flush_category()
                subtitle_tag = node.find("p", class_="body")
                subtitle = clean_text(subtitle_tag.get_text()) if subtitle_tag else ""
                current_category = {
                    "title":    clean_text(h2.get_text()),
                    "subtitle": subtitle,
                    "channels": [],
                    "is_adult": _is_adult_section(),
                }
            return  # não precisa descer; já extraímos o que queríamos

        # ── Destaque-banner (canais) ───────────────────────────────────────
        if "destaque-banner" in classes:
            if current_category is not None:
                channels = _extract_destaque_banner_channels(node)
                current_category["channels"].extend(channels)
            return  # não descer dentro do banner

        # ── Desce nos outros nós ──────────────────────────────────────────
        for child in node.children:
            if isinstance(child, Tag):
                walk_for_categories(child)

    walk_for_categories(body)
    _flush_category()

    # ── Link do modal adulto ───────────────────────────────────────────────
    result["adult_modal_link"] = _extract_adult_modal_link(soup)

    # ── Legaltext ─────────────────────────────────────────────────────────
    result["legaltext"] = _extract_legaltext(soup)

    return result


# ──────────────────────────────────────────────────────────────────────────────
# Geração do arquivo .txt estruturado
# ──────────────────────────────────────────────────────────────────────────────

def _fmt_channel(ch: dict, col_label: int = 12) -> str:
    """Formata um canal no estilo do arquivo de referência."""
    lines = []
    lines.append(ch["name"])

    desc = ch["description"]
    if desc:
        lines.append(f"  {'Descrição':<{col_label}}: {desc}")

    price = ch["price"]
    if price:
        lines.append(f"  {'Preço':<{col_label}}: {price}")

    href = ch["href"]
    if href:
        lines.append(f"  {'Link':<{col_label}}: {href}")

    return "\n".join(lines)


def build_structured_txt(meta: dict, data: dict) -> str:
    """Constrói o conteúdo completo do .txt estruturado."""
    lines: list[str] = []

    # ── Cabeçalho ──────────────────────────────────────────────────────────
    title = data["page_title"] or meta.get("title", "")
    page_source = meta.get("title", "")  # "Canais Adicionais – Complete seu pacote! | Vivo"
    lines.append(SEP_FULL)
    lines.append(f"{page_source.upper()}")
    lines.append(SEP_FULL)
    lines.append("")

    if data["intro"]:
        lines.append(data["intro"])
        lines.append("")

    # ── Descrição da página (meta) ─────────────────────────────────────────
    if meta.get("description") and meta["description"] != data["intro"]:
        lines.append(meta["description"])
        lines.append("")

    # ── Como contratar ─────────────────────────────────────────────────────
    if data["how_to_hire"]:
        lines.append("COMO CONTRATAR:")
        for item in data["how_to_hire"]:
            lines.append(f"- {item}")
        lines.append("")

    # ── Lista de categorias disponíveis ────────────────────────────────────
    if data["categories"]:
        cat_names = " | ".join(c["title"] for c in data["categories"])
        lines.append(SEP_FULL)
        lines.append(f"CATEGORIAS DISPONÍVEIS:")
        lines.append(f"  {cat_names}")
        lines.append(SEP_FULL)
        lines.append("")
        lines.append("")

    # ── Seções por categoria ────────────────────────────────────────────────
    for cat in data["categories"]:
        lines.append(SEP_HALF)
        lines.append(cat["title"].upper())
        lines.append(SEP_HALF)

        if cat["subtitle"]:
            lines.append(cat["subtitle"])
        lines.append("")

        # Seção adultos: aviso especial + link do modal
        if cat["is_adult"]:
            if data["adult_modal_link"]:
                lines.append(f"  AVISO: A página pode conter imagens impróprias para menores de 18 anos.")
                lines.append(f"  Acesso restrito a maiores de 18 anos.")
                lines.append(f"  Link de acesso: {data['adult_modal_link']}")
                lines.append("")

        for ch in cat["channels"]:
            lines.append(_fmt_channel(ch))
            lines.append("")

    # ── Atenção / Legaltext ────────────────────────────────────────────────
    if data["legaltext"]:
        lines.append("")
        lines.append(SEP_FULL)
        lines.append("Atenção")
        lines.append(SEP_FULL)
        for lt in data["legaltext"]:
            lines.append(lt)
        lines.append(SEP_FULL)

    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Persistência
# ──────────────────────────────────────────────────────────────────────────────

def _category_to_folder(category: str) -> str:
    """Mesmo algoritmo do scrapertxt.py para manter pastas consistentes."""
    s = category.lower()
    s = re.sub(r"[—–]", "-", s)
    s = s.translate(str.maketrans("ãâáàêéèíîõôóúûç ", "aaaaeeeiiooouuc-"))
    s = re.sub(r"[^a-z0-9-]", "", s)
    return re.sub(r"-+", "-", s).strip("-")


def save_structured_txt(slug: str, meta: dict, data: dict) -> Path:
    entry  = get_entry(slug)
    folder = OUTPUT_DIR / _category_to_folder(entry["category"])
    folder.mkdir(parents=True, exist_ok=True)
    path   = folder / f"{slug}-structured.txt"
    content = build_structured_txt(meta, data)
    path.write_text(content, encoding="utf-8")
    return path


# ──────────────────────────────────────────────────────────────────────────────
# Processamento de uma página
# ──────────────────────────────────────────────────────────────────────────────

async def process_page(page, slug: str) -> bool:
    url   = build_url(slug)
    entry = get_entry(slug)
    print(f"\n🌐 [{slug}]\n   URL      : {url}\n   Categoria: {entry['category']}")

    soup = await fetch_main_content(page, url)
    if soup is None:
        print("   ❌ Não foi possível obter o conteúdo.")
        return False

    meta = extract_meta(soup)
    data = extract_structured_sections(soup)
    txt_path = save_structured_txt(slug, meta, data)

    n_channels = sum(len(c["channels"]) for c in data["categories"])
    print(
        f"   ✅ Título    : {meta['title'] or '(sem título)'}\n"
        f"   📑 Categorias: {len(data['categories'])}\n"
        f"   📺 Canais    : {n_channels}\n"
        f"   💾 Arquivo   : {txt_path.relative_to(Path(__file__).parent)}"
    )
    return True


# ──────────────────────────────────────────────────────────────────────────────
# Entrada principal
# ──────────────────────────────────────────────────────────────────────────────

async def main(slugs: list[str]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"🚀 scrapertxt-structured.py — {len(slugs)} página(s) para processar\n"
          f"   Saída: {OUTPUT_DIR.resolve()}\n")

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
        ok = fail = 0
        for i, slug in enumerate(slugs, 1):
            print(f"── [{i}/{len(slugs)}] ─────────────────────────────")
            try:
                ok += await process_page(pg, slug)
            except Exception as e:
                print(f"   ❌ Erro inesperado em [{slug}]: {e}")
                fail += 1
        await browser.close()

    print(
        f"\n{'═'*50}\n"
        f"🎉 Concluído!  ✅ {ok} ok   ❌ {fail} falhas   📄 {len(slugs)} total\n"
        f"   TXTs salvos em: {OUTPUT_DIR.resolve()}"
    )


def parse_args(argv: list[str]) -> tuple[list[str], bool]:
    show_list     = "--list" in argv
    argv_clean    = [a for a in argv if a != "--list"]
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
    all_slugs  = get_all_slugs()

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
        print(f"\n📋 Catálogo de páginas ({len(slugs_to_run)} páginas)\n")
        print_list(slugs_to_run)
        print(f"\n  Total: {len(slugs_to_run)} páginas em {len(get_categories())} categorias\n")
        sys.exit(0)
    asyncio.run(main(slugs_to_run))