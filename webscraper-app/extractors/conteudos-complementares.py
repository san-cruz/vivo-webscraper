"""extractors/conteudos-complementares.py — Conteúdos Complementares

Cobre as três páginas da categoria:

  apps-inclusos-no-plano-de-internet
    highlight-product (h1 + richtext intro) →
    side-by-side × 3 (cards de apps) → title (h2) + side-by-side →
    banner-secondary → title (h3) + faq-container →
    legaltext × 2 → title (h3) + cross →
    title (h2 "LIONSGATE+") + comunicados

  vivo-smart-wi-fi
    banner--campanha (banner__text + CTA "Baixar Vivo Smart Wi-Fi") →
    title (h2) + steps-feature (7 funcionalidades) →
    photo-text-component × 3 → title (h2) + faq-container →
    title (h2) + cross → legaltext

  beneficios-vivo-tv
    title (h1) + comunicados →
    photo-text-component × 5 →
    title (h3 + p.body "soluções de acessibilidade") + side-by-side →
    tabs-component (Closed Caption + Audiodescrição com steps) →
    steps-feature × 2 (avulsos) →
    title (h2) + button-component ("Consultar ofertas") +
      online-store (Stick, Streamings, Canais) + destaque-banner →
    title (h2) + cross
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
    handle_end_of_page, handle_button_component,
    handle_banner_campanha,
    handle_p_standalone,
    _extract_card_blocks, append_to_last_section,
)


def handle_online_store_complementar(node: Tag, sections: list, visited: set) -> bool:
    """
    Extrai online-store-container-component como lista de cards.
    Diferente do handle_online_store de por-que-vivo.py (que bloqueia),
    aqui os itens são dispositivos/serviços complementares informativos
    (ex: Stick Vivo TV, Streamings, Canais adicionais em beneficios-vivo-tv).
    """
    if "online-store-container-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    card_groups = []
    for item in node.find_all("div", class_="online-store-component"):
        pi = item.find("div", class_="product-item")
        if not pi:
            continue
        blocks = _extract_card_blocks(pi)
        if blocks:
            card_groups.append(blocks)

    if not card_groups:
        return True

    result = []
    for i, group in enumerate(card_groups):
        if i > 0:
            result.append({"type": "blank"})
        result.extend(group)
    append_to_last_section(sections, result)
    return True


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
    visited_button:    set[int] = set()
    visited_campanha:  set[int] = set()
    visited_store:     set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag):
            return

        # ── Banner hero (vivo-smart-wi-fi: texto + CTA antes do h2) ───────
        if handle_banner_campanha(node, sections, visited_campanha):       return

        # ── Componentes de destaque / banners ──────────────────────────────
        if handle_highlight_product(node, sections, visited_highlight):    return
        if handle_banner_secondary(node, sections, visited_banner):        return
        if handle_slick_cards(node, sections, visited_slick):              return
        if handle_destaque_banner(node, sections, visited_destaque):       return

        # ── FAQ / acordeão ─────────────────────────────────────────────────
        if handle_faq_container(node, sections, visited_faq):              return
        if handle_accordion_standalone(node, sections, visited_faq):       return

        # ── Abas e passos ──────────────────────────────────────────────────
        if handle_tabs_component(node, sections, visited_tabs, visited_steps): return
        if handle_steps_standalone(node, sections, visited_steps):         return

        # ── Teaser (photo-text-component) ──────────────────────────────────
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

        # ── Vitrine de produtos/serviços complementares (extrair) ──────────
        if handle_online_store_complementar(node, sections, visited_store): return

        # ── Botões CTA avulsos (ex: "Consultar ofertas") ───────────────────
        if handle_button_component(node, sections, visited_button):        return

        # ── Acesso rápido ──────────────────────────────────────────────────
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