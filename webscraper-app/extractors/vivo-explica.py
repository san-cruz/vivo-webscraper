"""extractors/vivo-explica.py — Vivo Explica

Cobre as três páginas da categoria:
  - explica-internet-wifi       → página de categoria (teaser destaque + steps + side-by-side + acesso-rapido)
  - explica-smartphones-eletronicos → mesma estrutura de categoria
  - explica-dicionario-velocidade → artigo longo (highlight-product + h2 + comunicados + photo-text teaser + video-component + cross)

Estrutura típica das páginas de categoria (internet-e-wi-fi, smartphones-eletronicos):
  highlight-product? | title (h1) → photo-text-component (teaser destaque) →
  title (h2) + side-by-side-component (cards de novidades) →
  steps-feature (mais lidas) → side-by-side-component (dicas) →
  acesso-rapido (outras categorias)

Estrutura típica dos artigos (dicionario-de-velocidade):
  highlight-product → comunicados (intro) → nav-links (índice âncoras — links # ignorados) →
  [title (h2) + comunicados | photo-text-component (teaser)] * N →
  video-component (ignorado — sem texto útil) → cross

Todos os handlers necessários já existem em extractors/base.py.
O video-component não possui conteúdo textual e é naturalmente ignorado pelo walker
(não coincide com nenhum handler e não tem filhos capturáveis).
"""

from bs4 import BeautifulSoup, Tag
from extractors.base import (
    _extract_page_title_section, make_faq_duplicate_checker,
    handle_comunicados, handle_richtext,
    handle_side_by_side_component, handle_side_by_side_row,
    handle_slick_cards, handle_banner_secondary, handle_highlight_product,
    handle_nav_links, handle_legaltext,
    handle_tabs_component, handle_faq_container, handle_accordion_standalone,
    handle_teaser, handle_acesso_rapido,
    handle_see_all, handle_cross,
    handle_h2, handle_h3, handle_p_h2, handle_p_h3,
    handle_destaque_banner, handle_steps_standalone,
    handle_end_of_page, handle_p_standalone,
)


def extract_sections(soup: BeautifulSoup, page_url: str = "") -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    is_faq_duplicate = make_faq_duplicate_checker(soup)

    visited_tabs:      set[int] = set()
    visited_teasers:   set[int] = set()
    visited_headings:  set[int] = set()
    visited_faq:       set[int] = set()
    visited_end:       set[int] = set()
    visited_steps:     set[int] = set()
    visited_slick:     set[int] = set()
    visited_cross:     set[int] = set()
    visited_banner:    set[int] = set()
    visited_see_all:   set[int] = set()
    visited_highlight: set[int] = set()
    visited_destaque:  set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag):
            return

        # ── Componentes de destaque / banners ──────────────────────────────
        if handle_highlight_product(node, sections, visited_highlight):   return
        if handle_banner_secondary(node, sections, visited_banner):        return
        if handle_slick_cards(node, sections, visited_slick):              return
        if handle_destaque_banner(node, sections, visited_destaque):       return

        # ── FAQ / acordeão ─────────────────────────────────────────────────
        if handle_faq_container(node, sections, visited_faq):              return
        if handle_accordion_standalone(node, sections, visited_faq):       return

        # ── Abas e passos ──────────────────────────────────────────────────
        if handle_tabs_component(node, sections, visited_tabs, visited_steps): return
        if handle_steps_standalone(node, sections, visited_steps):         return

        # ── Teaser (photo-text-component): usa richtext completo para capturar
        #    parágrafos, listas e botões dentro dos artigos do Vivo Explica ──
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=True): return

        # ── Navegação / ver mais ───────────────────────────────────────────
        if handle_see_all(node, sections, visited_see_all):                return

        # ── Títulos e subtítulos ───────────────────────────────────────────
        if handle_h2(node, sections, visited_headings, is_faq_duplicate):  return
        if handle_h3(node, sections, visited_headings):                    return
        if handle_p_h2(node, sections, visited_headings):                  return
        if handle_p_h3(node, sections, visited_headings):                  return

        # ── Blocos de texto rico ───────────────────────────────────────────
        if handle_richtext(node, sections):                                return
        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=True): return

        # ── Cards e listas laterais ────────────────────────────────────────
        if handle_side_by_side_component(node, sections):                  return
        if handle_side_by_side_row(node, sections):                        return

        # ── Acesso rápido (outras categorias do Vivo Explica) ─────────────
        if handle_acesso_rapido(node, sections, page_url=page_url):        return

        # ── Cross-sell e links auxiliares ─────────────────────────────────
        if handle_cross(node, sections, visited_cross):                    return
        if handle_nav_links(node, sections):                               return
        if handle_legaltext(node, sections):                               return

        # ── Fim de página ──────────────────────────────────────────────────
        if handle_end_of_page(node, sections, visited_end):               return

        # ── Parágrafos avulsos ─────────────────────────────────────────────
        if handle_p_standalone(node, sections):                            return

        for child in node.children:
            if isinstance(child, Tag):
                walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag):
            walk(child)

    return [s for s in sections if s.get("title") or s.get("blocks")]