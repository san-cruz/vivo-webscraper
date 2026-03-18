"""
extractors/ajuda-e-autoatendimento.py
--------------------------------------
Extractor especializado para a categoria "Ajuda e Autoatendimento".

Estrutura tipica dessas paginas -- variada, combinando elementos de
ativacao e duvidas:
  - h1 titulo
  - tabs-component com passos (ex: portabilidade, ativando-o-chip)
  - faq-container-component / ul.accordion avulso com FAQs
  - teaser de icones ou com richtext (beneficios, recursos)
  - richtext / comunicados com texto informativo
  - steps-feature avulsos (fora de tabs)
  - slick-slider com cards (ex: app-vivo)
  - banner-secondary-container-component (banners rotativos)
  - side-by-side-component (cards de feature / SMS)
  - acesso-rapido (cards de navegacao, incluindo ancoras da propria pagina)
  - see-all-component (vermais -- titulo + link para secao)
  - cross (cards de cross-sell)
  - nav-links (links de documentos/termos)
  - legaltext-component (texto legal)
  - end-of-page (links para outras secoes de ajuda)

Decisoes de design:
  - extract_sections recebe page_url opcional para resolver ancoras relativas
    (#cobertura -> https://vivo.com.br/.../dicas-wifi#cobertura)
  - handle_see_all antes de handle_h2: evita que o h2 do vermais__title
    seja registrado como secao isolada antes de ser associado ao link.
"""

from bs4 import BeautifulSoup, Tag

import re as _re

from extractors.base import (
    _extract_page_title_section,
    make_faq_duplicate_checker,
    handle_comunicados,
    handle_richtext,
    handle_side_by_side_component,
    handle_side_by_side_row,
    handle_slick_cards,
    handle_banner_secondary,
    handle_highlight_product,
    handle_nav_links,
    handle_legaltext,
    handle_tabs_component,
    handle_faq_container,
    handle_accordion_standalone,
    handle_teaser,
    handle_acesso_rapido,
    handle_see_all,
    handle_cross,
    handle_h2,
    handle_h3,
    handle_p_h2,
    handle_p_h3,
    handle_destaque_banner,
    handle_steps_standalone,
    handle_end_of_page,
    handle_p_standalone,
)


def extract_sections(soup: BeautifulSoup, page_url: str = "") -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    is_faq_duplicate = make_faq_duplicate_checker(soup)

    visited_tabs:     set[int] = set()
    visited_teasers:  set[int] = set()
    visited_headings: set[int] = set()
    visited_faq:      set[int] = set()
    visited_end:      set[int] = set()
    visited_steps:    set[int] = set()
    visited_slick:    set[int] = set()
    visited_cross:    set[int] = set()
    visited_banner:   set[int] = set()
    visited_see_all:   set[int] = set()
    visited_highlight:  set[int] = set()
    visited_destaque:   set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag):
            return

        # Carrosseis e banners
        if handle_highlight_product(node, sections, visited_highlight):
            return
        if handle_banner_secondary(node, sections, visited_banner):
            return
        if handle_slick_cards(node, sections, visited_slick):
            return
        if handle_destaque_banner(node, sections, visited_destaque):
            return

        # Componentes de FAQ
        if handle_faq_container(node, sections, visited_faq):
            return
        if handle_accordion_standalone(node, sections, visited_faq):
            return

        # Componentes de passos
        if handle_tabs_component(node, sections, visited_tabs, visited_steps):
            return
        if handle_steps_standalone(node, sections, visited_steps):
            return

        # Teaser
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=True):
            return

        # See-all (vermais) ANTES de handle_h2 para capturar o link
        if handle_see_all(node, sections, visited_see_all):
            return

        # Titulos avulsos
        if handle_h2(node, sections, visited_headings, is_faq_duplicate):
            return
        if handle_h3(node, sections, visited_headings):
            return
        if handle_p_h2(node, sections, visited_headings):
            return
        if handle_p_h3(node, sections, visited_headings):
            return

        # Conteudo textual rico
        if handle_richtext(node, sections):
            return
        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=True):
            return

        # Componentes de layout
        if handle_side_by_side_component(node, sections):
            return
        if handle_side_by_side_row(node, sections):
            return
        if handle_acesso_rapido(node, sections, page_url=page_url):
            return
        if handle_cross(node, sections, visited_cross):
            return
        if handle_nav_links(node, sections):
            return
        if handle_legaltext(node, sections):
            return

        # Rodape
        if handle_end_of_page(node, sections, visited_end):
            return

        # Paragrafo avulso
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