"""
extractors/duvidas-internet-tv.py
----------------------------------
Extractor especializado para as categorias:
  - "Dúvidas — Internet"  (duvidas-internet-wifi, duvidas-internet-fibra,
                            duvidas-internet-vivo-total)
  - "Dúvidas — TV"        (duvidas-tv-fibra, duvidas-tv-apps-canais,
                            duvidas-tv-assinatura, duvidas-tv-online)

Estrutura das páginas:
  - h1 título
  - faq-container-component: múltiplos ul.accordion agrupados em um único bloco FAQ
    · ol > li nas respostas → N.1. item, N.2. item
    · ul > li nas respostas → - item
    · p                     → parágrafo
  - Seções de conteúdo misto (teaser, richtext com lista, botões CTA)
  - Cards de navegação com link (Vivo Explica, Dúvidas sobre outro assunto)
  - end-of-page
"""

from bs4 import BeautifulSoup, Tag

from extractors.base import (
    _extract_page_title_section,
    handle_faq_container,
    handle_accordion_standalone,
    handle_teaser,
    handle_h2,
    handle_h3,
    handle_p_h2,
    handle_richtext,
    handle_comunicados,
    handle_side_by_side_component,
    handle_acesso_rapido,
    handle_end_of_page,
    handle_p_standalone,
    make_faq_duplicate_checker,
)


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    # Duvidas não têm o padrão de duplicata mobile/desktop, mas o checker
    # é inofensivo e mantém a interface uniforme entre extractors.
    is_faq_duplicate = make_faq_duplicate_checker(soup)

    visited_faq:      set[int] = set()
    visited_headings: set[int] = set()
    visited_teasers:  set[int] = set()
    visited_end:      set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag):
            return

        if handle_faq_container(node, sections, visited_faq):
            return
        if handle_accordion_standalone(node, sections, visited_faq):
            return
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=True):
            return
        if handle_h2(node, sections, visited_headings):
            return
        if handle_h3(node, sections, visited_headings):
            return
        if handle_p_h2(node, sections, visited_headings):
            return
        if handle_richtext(node, sections):
            return
        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=True):
            return
        if handle_side_by_side_component(node, sections):
            return
        if handle_acesso_rapido(node, sections):
            return
        if handle_end_of_page(node, sections, visited_end):
            return
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