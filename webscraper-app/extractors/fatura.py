"""extractors/fatura.py — Categoria Fatura"""

from bs4 import BeautifulSoup, Tag
from extractors.base import (
    _extract_page_title_section, _inline_links, _normalize_href, clean_text,
    make_faq_duplicate_checker, append_to_last_section,
    handle_comunicados, handle_richtext, handle_side_by_side_component,
    handle_nav_links, handle_legaltext, handle_teaser, handle_tabs_component,
    handle_faq_container, handle_accordion_standalone, handle_see_all, handle_cross,
    handle_h2, handle_h3, handle_p_h2, handle_steps_standalone,
    handle_end_of_page, handle_button_component, handle_p_standalone,
)


def handle_list_component(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    classes = node.get("class", [])
    is_list = node.get("data-controller") == "list" or ("secondary-components" in classes and node.find("div", class_="list__item"))
    if not is_list or id(node) in visited: return False
    visited.add(id(node))
    list_text = node.find("div", class_="list-text")
    title = clean_text(list_text.find(["h2","h3","h4"]).get_text()) if list_text and list_text.find(["h2","h3","h4"]) else ""
    ordered_items, paragraph_items = [], []
    for item_div in node.find_all("div", class_="list__item"):
        richtext = item_div.find("div", class_="richtext")
        if not richtext: continue
        if "numbered" in richtext.get("class", []):
            body_div = richtext.find("div", class_="body")
            item_title = clean_text(body_div.get_text()) if body_div else ""
            description = " ".join(_inline_links(p) for p in richtext.find_all("p") if _inline_links(p))
            if item_title and description: ordered_items.append(f"{item_title}: {description}")
            elif item_title: ordered_items.append(item_title)
            elif description: ordered_items.append(description)
        else:
            paragraph_items.extend({"type":"paragraph","text":t} for p in richtext.find_all("p") if (t := _inline_links(p)))
    blocks = ([{"type":"ordered","items":ordered_items}] if ordered_items else []) + paragraph_items
    if title: sections.append({"title": title, "blocks": blocks})
    elif blocks: append_to_last_section(sections, blocks)
    return True


def handle_end_page(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    if "end-page" not in node.get("class", []) or id(node) in visited: return False
    visited.add(id(node))
    groups = []
    for a in node.find_all("a", class_="end-page__item", href=True):
        href = _normalize_href(a["href"].strip())
        if not href or href == "#": continue
        content, btn_span = a.find("div", class_="end-page__item__content"), a.find("span", class_="h4")
        parts = [clean_text(p.get_text()) for p in content.find_all("p") if clean_text(p.get_text())] if content else []
        btn_text = clean_text(btn_span.get_text()) if btn_span else ""
        line = " - ".join(parts)
        line = (f"{line} {btn_text} Link: {href}" if line else f"{btn_text} Link: {href}") if btn_text else (f"{line} Link: {href}" if line else f"Link: {href}")
        if line: groups.append({"type":"paragraph","text":line})
    if groups: append_to_last_section(sections, groups)
    return True


def handle_table_component(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    if "table-component" not in node.get("class", []) or id(node) in visited: return False
    visited.add(id(node))
    table = node.find("table")
    if not table: return True
    rows = [[clean_text(td.get_text()) for td in tr.find_all(["td","th"])] for tr in table.find_all("tr")]
    rows = [[c for c in r if c] for r in rows if any(r)]
    if not rows: return True
    header, data_rows = rows[0], rows[1:] if len(rows) > 1 else rows
    items = []
    if len(header) >= 2 and data_rows:
        append_to_last_section(sections, [{"type":"heading","text":" × ".join(header)}])
        items = [f"{r[0]}: {r[1]}" if len(r) >= 2 else r[0] for r in data_rows]
    else:
        items = [" - ".join(r) for r in (data_rows or rows)]
    if items: append_to_last_section(sections, [{"type":"unordered","items":items}])
    return True


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    sections = list(_extract_page_title_section(soup))
    is_faq_duplicate = make_faq_duplicate_checker(soup)
    visited_tabs: set[int] = set()
    visited_teasers: set[int] = set()
    visited_headings: set[int] = set()
    visited_faq: set[int] = set()
    visited_end: set[int] = set()
    visited_end_page: set[int] = set()
    visited_button: set[int] = set()
    visited_steps: set[int] = set()
    visited_cross: set[int] = set()
    visited_see_all: set[int] = set()
    visited_list: set[int] = set()
    visited_table: set[int] = set()

    def walk(node: Tag) -> None:
        if not isinstance(node, Tag): return
        if handle_faq_container(node, sections, visited_faq): return
        if handle_accordion_standalone(node, sections, visited_faq): return
        if handle_tabs_component(node, sections, visited_tabs, visited_steps): return
        if handle_steps_standalone(node, sections, visited_steps): return
        if handle_list_component(node, sections, visited_list): return
        if handle_table_component(node, sections, visited_table): return
        if handle_teaser(node, sections, visited_teasers, use_richtext_full=True): return
        if handle_see_all(node, sections, visited_see_all): return
        if handle_h2(node, sections, visited_headings, is_faq_duplicate): return
        if handle_h3(node, sections, visited_headings): return
        if handle_p_h2(node, sections, visited_headings): return
        if handle_richtext(node, sections): return
        if handle_comunicados(node, sections, is_faq_duplicate, use_richtext_full=True): return
        if handle_side_by_side_component(node, sections): return
        if handle_cross(node, sections, visited_cross): return
        if handle_nav_links(node, sections): return
        if handle_legaltext(node, sections): return
        if handle_end_of_page(node, sections, visited_end): return
        if handle_end_page(node, sections, visited_end_page): return
        if handle_button_component(node, sections, visited_button): return
        if handle_p_standalone(node, sections): return
        for child in node.children:
            if isinstance(child, Tag): walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag): walk(child)
    return [s for s in sections if s.get("title") or s.get("blocks")]