"""
extractors/fatura.py
---------------------
Extractor especializado para a categoria "Fatura".

Páginas cobertas:
  2-via-de-fatura, entenda-sua-fatura, fatura-digital,
  debito-automatico, negociacao-de-debitos, pagamento, bloqueio-de-linha

Estrutura típica dessas páginas:
  - h1 título (banner highlight-product-component)
  - h2/h3 avulsos dentro de div.title
  - div.comunicados com richtext (parágrafos, ol, ul)
  - div.richtext avulso com texto informativo
  - data-controller="list" — lista numerada com título lateral (div.list-text)
    e itens div.list__item > div.richtext.numbered (span com número + corpo)
  - div.teaser.teaser--half-image — banner lateral com CTA
  - div.faq-container-component / ul.accordion — FAQs
  - div.see-all-component (vermais) — seção com link
  - div.cross — cards de cross-sell
  - div.end-of-page-component — links de rodapé (end-page__item)
  - div.end-page (data-controller="endPage") — CTA de rodapé estilo banner
  - div.table-component — tabela (ex: vencimento × renovação de franquia)
  - div.nav-links — links de documentos/termos
  - div.legaltext-component — texto legal
  - div.side-by-side-component — cards de feature (vantagens)

Componentes únicos desta categoria:
  handle_list_component  — data-controller="list": título lateral + itens numerados
  handle_end_page        — div.end-page (endPage): CTA banner de rodapé
  handle_table_component — div.table-component: tabela HTML → lista de pares
"""

from bs4 import BeautifulSoup, NavigableString, Tag

from extractors.base import (
    _extract_page_title_section,
    _inline_links,
    _normalize_href,
    clean_text,
    make_faq_duplicate_checker,
    append_to_last_section,
    handle_comunicados,
    handle_richtext,
    handle_side_by_side_component,
    handle_nav_links,
    handle_legaltext,
    handle_teaser,
    handle_tabs_component,
    handle_faq_container,
    handle_accordion_standalone,
    handle_see_all,
    handle_cross,
    handle_h2,
    handle_h3,
    handle_p_h2,
    handle_steps_standalone,
    handle_end_of_page,
    handle_p_standalone,
)


# ──────────────────────────────────────────────
# Handlers exclusivos da categoria Fatura
# ──────────────────────────────────────────────

def handle_list_component(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa o componente data-controller="list" (div.row.secondary-components).

    Estrutura HTML:
      div.row.secondary-components[data-controller="list"]
        div.list-text
          p.overline          ← eyebrow (geralmente vazio)
          h2|h3.h2|h3        ← título lateral da lista
        div (col-xl-8)
          div.list__item
            div.richtext.bullets.numbered
              span            ← número (ex: "1")
              div.body | p    ← título do item
              p               ← descrição do item (opcional)

    Gera uma nova seção com título extraído de div.list-text e
    uma lista ordenada com "Título do item: descrição" por item.
    Items sem numeração (div.richtext.bullets sem .numbered) são
    emitidos como parágrafos simples dentro da mesma seção.
    """
    classes = node.get("class", [])
    controller = node.get("data-controller", "")
    is_list = controller == "list" or (
        "secondary-components" in classes
        and node.find("div", class_="list__item")
    )
    if not is_list or id(node) in visited:
        return False
    visited.add(id(node))

    # Título lateral
    list_text = node.find("div", class_="list-text")
    title = ""
    if list_text:
        h_tag = list_text.find(["h2", "h3", "h4"])
        if h_tag:
            title = clean_text(h_tag.get_text())

    # Itens
    ordered_items: list[str] = []
    paragraph_items: list[dict] = []

    for item_div in node.find_all("div", class_="list__item"):
        richtext = item_div.find("div", class_="richtext")
        if not richtext:
            continue

        is_numbered = "numbered" in richtext.get("class", [])

        if is_numbered:
            # Título do item: div.body ou primeiro <p> não-vazio
            body_div = richtext.find("div", class_="body")
            if body_div:
                item_title = clean_text(body_div.get_text())
            else:
                item_title = ""

            # Descrição: todos os <p> (excluindo vazios e <sub> isolado)
            desc_parts = []
            for p in richtext.find_all("p"):
                text = _inline_links(p)
                if text:
                    desc_parts.append(text)
            description = " ".join(desc_parts)

            if item_title and description:
                ordered_items.append(f"{item_title}: {description}")
            elif item_title:
                ordered_items.append(item_title)
            elif description:
                ordered_items.append(description)

        else:
            # Item sem numeração → parágrafo simples
            for p in richtext.find_all("p"):
                text = _inline_links(p)
                if text:
                    paragraph_items.append({"type": "paragraph", "text": text})

    # Monta os blocos da seção
    blocks: list[dict] = []
    if ordered_items:
        blocks.append({"type": "ordered", "items": ordered_items})
    blocks.extend(paragraph_items)

    if title:
        sections.append({"title": title, "blocks": blocks})
    elif blocks:
        append_to_last_section(sections, blocks)

    return True


def handle_end_page(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.end-page (data-controller="endPage") — CTA banner de rodapé.

    Estrutura HTML:
      div.end-page.end-page--colorpicker[data-controller="endPage"]
        div.container > div.row > div.col-xl-12
          a.end-page__item[href]
            div.end-page__item__content
              p.body          ← título do CTA (ex: "App Vivo")
              p.body-2        ← descrição (opcional)
            span.h4.links-    ← texto do botão (ex: "Acessar App Vivo")

    Gera um parágrafo "Título - Descrição Texto_botão Link: href".
    Múltiplos end-page na mesma página são emitidos com blank entre si.
    """
    if "end-page" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    groups: list[dict] = []

    for a in node.find_all("a", class_="end-page__item", href=True):
        href = _normalize_href(a["href"].strip())
        if not href or href == "#":
            continue

        content = a.find("div", class_="end-page__item__content")
        btn_span = a.find("span", class_="h4")

        parts = []
        if content:
            for p in content.find_all("p"):
                text = clean_text(p.get_text())
                if text:
                    parts.append(text)

        btn_text = clean_text(btn_span.get_text()) if btn_span else ""

        line = " - ".join(parts)
        if btn_text:
            line = f"{line} {btn_text} Link: {href}" if line else f"{btn_text} Link: {href}"
        else:
            line = f"{line} Link: {href}" if line else f"Link: {href}"

        if line:
            groups.append({"type": "paragraph", "text": line})

    if groups:
        append_to_last_section(sections, groups)
    return True


def handle_table_component(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.table-component (tabela HTML renderizada pelo datatable).

    Estrutura HTML:
      div.table-component
        div.container.table--original[data-controller="filter"]
          div.table__datatable[data-controller="datatable"]
            table > tbody > tr > td

    Converte a tabela em lista não-ordenada de "ColA: ColB" por linha
    (excluindo a linha de cabeçalho). Se houver cabeçalho (primeira linha),
    usa-o para rotular as colunas.

    Exemplo de saída para a tabela de vencimentos em pagamento.html:
      - Dia 01: Dia 16
      - Dia 06: Dia 21
      ...
    """
    if "table-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    table = node.find("table")
    if not table:
        return True

    rows = []
    for tr in table.find_all("tr"):
        cells = [clean_text(td.get_text()) for td in tr.find_all(["td", "th"])]
        cells = [c for c in cells if c]
        if cells:
            rows.append(cells)

    if not rows:
        return True

    # Primeira linha = cabeçalho
    header = rows[0] if rows else []
    data_rows = rows[1:] if len(rows) > 1 else rows

    items: list[str] = []

    if len(header) >= 2 and data_rows:
        # Emite cabeçalho como heading para contextualizar a tabela
        heading_text = " × ".join(header)
        append_to_last_section(sections, [{"type": "heading", "text": heading_text}])
        for row in data_rows:
            if len(row) >= 2:
                items.append(f"{row[0]}: {row[1]}")
            elif row:
                items.append(row[0])
    else:
        for row in data_rows or rows:
            items.append(" - ".join(row))

    if items:
        append_to_last_section(sections, [{"type": "unordered", "items": items}])

    return True


# ──────────────────────────────────────────────
# Extractor principal
# ──────────────────────────────────────────────

def extract_sections(soup: BeautifulSoup) -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    is_faq_duplicate = make_faq_duplicate_checker(soup)

    visited_tabs:     set[int] = set()
    visited_teasers:  set[int] = set()
    visited_headings: set[int] = set()
    visited_faq:      set[int] = set()
    visited_end:      set[int] = set()
    visited_end_page: set[int] = set()
    visited_steps:    set[int] = set()
    visited_cross:    set[int] = set()
    visited_see_all:  set[int] = set()
    visited_list:     set[int] = set()
    visited_table:    set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag):
            return

        # ── Componentes FAQ ──────────────────────────────────────────────
        if handle_faq_container(node, sections, visited_faq):
            return
        if handle_accordion_standalone(node, sections, visited_faq):
            return

        # ── Passos ───────────────────────────────────────────────────────
        if handle_tabs_component(node, sections, visited_tabs, visited_steps):
            return
        if handle_steps_standalone(node, sections, visited_steps):
            return

        # ── Listas numeradas (list-component) ────────────────────────────
        if handle_list_component(node, sections, visited_list):
            return

        # ── Tabela ───────────────────────────────────────────────────────
        if handle_table_component(node, sections, visited_table):
            return

        # ── Teaser ───────────────────────────────────────────────────────
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=True):
            return

        # ── See-all (vermais) ANTES de handle_h2 ────────────────────────
        if handle_see_all(node, sections, visited_see_all):
            return

        # ── Títulos avulsos ──────────────────────────────────────────────
        if handle_h2(node, sections, visited_headings, is_faq_duplicate):
            return
        if handle_h3(node, sections, visited_headings):
            return
        if handle_p_h2(node, sections, visited_headings):
            return

        # ── Conteúdo textual ─────────────────────────────────────────────
        if handle_richtext(node, sections):
            return
        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=True):
            return

        # ── Layout / componentes de feature ─────────────────────────────
        if handle_side_by_side_component(node, sections):
            return
        if handle_cross(node, sections, visited_cross):
            return
        if handle_nav_links(node, sections):
            return
        if handle_legaltext(node, sections):
            return

        # ── Rodapé ───────────────────────────────────────────────────────
        if handle_end_of_page(node, sections, visited_end):
            return
        if handle_end_page(node, sections, visited_end_page):
            return

        # ── Parágrafo avulso ─────────────────────────────────────────────
        if handle_p_standalone(node, sections):
            return

        for child in node.children:
            if isinstance(child, Tag):
                walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag):
            walk(child)

    return [s for s in sections if s.get("title") or s.get("blocks")]