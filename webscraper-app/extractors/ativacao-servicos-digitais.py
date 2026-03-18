"""
extractors/ativacao-servicos-digitais.py
-----------------------------------------
Extractor especializado para a categoria "Ativação de Serviços Digitais".

Páginas cobertas:
  ativacao-amazon-prime, ativacao-apple-music, ativacao-disney-plus,
  ativacao-globoplay, ativacao-max, ativacao-netflix, ativacao-premiere,
  ativacao-spotify, ativacao-telecine, ativacao-vivo-play, ativacao-vivae,
  ativacao-vale-saude, ativacao-mcafee, ativacao-ip-fixo-digital

Estrutura típica dessas páginas:
  - h1 título
  - tabs-component com abas de passos (Não tenho conta / Já tenho conta / etc.)
  - teaser de ícones (benefícios do serviço)
  - p.h2 + comunicados (Sobre mudanças dos meios de pagamento)
  - tabs-component com FAQs (Sobre o serviço / Pagamento / Acesso)
  - side-by-side-component ou div.row.side-by-side (cards de features)
  - div.nav-links (link de termos)
  - legaltext-component (texto legal)
  - end-of-page (link para outros tutoriais)
"""

from bs4 import BeautifulSoup, Tag

from extractors.base import (
    _extract_page_title_section,
    make_faq_duplicate_checker,
    handle_comunicados,
    handle_side_by_side_component,
    handle_side_by_side_row,
    handle_nav_links,
    handle_legaltext,
    handle_tabs_component,
    handle_teaser,
    handle_h2,
    handle_p_h2,
    handle_steps_standalone,
    handle_end_of_page,
    handle_p_standalone,
)


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    is_faq_duplicate = make_faq_duplicate_checker(soup)

    visited_tabs:     set[int] = set()
    visited_teasers:  set[int] = set()
    visited_headings: set[int] = set()
    visited_end:      set[int] = set()
    visited_steps:    set[int] = set()

    def walk(node: Tag):
        if not isinstance(node, Tag):
            return

        # Ordem dos handlers: do mais específico para o mais genérico

        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=False):
            return
        if handle_side_by_side_component(node, sections):
            return
        if handle_side_by_side_row(node, sections):
            return
        if handle_nav_links(node, sections):
            return
        if handle_legaltext(node, sections):
            return
        if handle_tabs_component(node, sections, visited_tabs, visited_steps):
            return
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=False):
            return
        if handle_h2(node, sections, visited_headings, is_faq_duplicate):
            return
        if handle_p_h2(node, sections, visited_headings):
            return
        if handle_steps_standalone(node, sections, visited_steps):
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