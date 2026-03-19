"""extractors/base.py — Módulo base compartilhado"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag

BASE_URL = "https://vivo.com.br"

PAGE_CATALOG: list[dict] = [
    # Ativação de Serviços Digitais
    *[{"slug": f"ativacao-{s}", "path": f"/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-{s}", "category": "Ativação de Serviços Digitais"}
      for s in ["amazon-prime","apple-music","disney-plus","globoplay","max","netflix","premiere","spotify","telecine","vivo-play","vivae","vale-saude","mcafee","ip-fixo-digital"]],
    # Ajuda e Autoatendimento
    {"slug": "app-vivo", "path": "/para-voce/app-vivo", "category": "Ajuda e Autoatendimento"},
    {"slug": "mais-ajuda", "path": "/para-voce/ajuda/mais-ajuda", "category": "Ajuda e Autoatendimento"},
    {"slug": "encontre-uma-loja", "path": "/para-voce/ajuda/mais-ajuda/encontre-uma-loja", "category": "Ajuda e Autoatendimento"},
    {"slug": "dicas-wifi", "path": "/para-voce/ajuda/autoatendimento/dicas-wifi", "category": "Ajuda e Autoatendimento"},
    {"slug": "mudanca-de-endereco", "path": "/para-voce/ajuda/autoatendimento/mudanca-de-endereco", "category": "Ajuda e Autoatendimento"},
    {"slug": "servico-de-instalacao", "path": "/para-voce/ajuda/autoatendimento/servico-de-instalacao", "category": "Ajuda e Autoatendimento"},
    {"slug": "portabilidade", "path": "/para-voce/ajuda/sou-novo-aqui/portabilidade", "category": "Ajuda e Autoatendimento"},
    {"slug": "ativando-o-chip", "path": "/para-voce/ajuda/sou-novo-aqui/ativando-o-chip", "category": "Ajuda e Autoatendimento"},
    {"slug": "consumo-de-internet", "path": "/para-voce/ajuda/sou-novo-aqui/consumo-de-internet", "category": "Ajuda e Autoatendimento"},
    # Fatura
    *[{"slug": s, "path": f"/para-voce/ajuda/minha-fatura/{s}", "category": "Fatura"}
      for s in ["2-via-de-fatura","entenda-sua-fatura","fatura-digital","debito-automatico","negociacao-de-debitos","pagamento","bloqueio-de-linha"]],
    # Dúvidas — Internet
    {"slug": "duvidas-internet-wifi", "path": "/para-voce/ajuda/duvidas/internet/internet-vivo-wi-fi", "category": "Dúvidas — Internet"},
    {"slug": "duvidas-internet-fibra", "path": "/para-voce/ajuda/duvidas/internet/internet-fibra", "category": "Dúvidas — Internet"},
    {"slug": "duvidas-internet-vivo-total", "path": "/para-voce/ajuda/duvidas/internet/internet-vivo-total", "category": "Dúvidas — Internet"},
    # Dúvidas — TV
    {"slug": "duvidas-tv-fibra", "path": "/para-voce/ajuda/duvidas/tv/tv-fibra", "category": "Dúvidas — TV"},
    {"slug": "duvidas-tv-apps-canais", "path": "/para-voce/ajuda/duvidas/tv/tv-apps-de-canais", "category": "Dúvidas — TV"},
    {"slug": "duvidas-tv-assinatura", "path": "/para-voce/ajuda/duvidas/tv/tv-assinatura", "category": "Dúvidas — TV"},
    {"slug": "duvidas-tv-online", "path": "/para-voce/ajuda/duvidas/tv/tv-online", "category": "Dúvidas — TV"},
    # Vivo Explica
    {"slug": "explica-internet-wifi", "path": "/para-voce/por-que-vivo/vivo-explica/internet-e-wi-fi", "category": "Vivo Explica"},
    {"slug": "explica-smartphones-eletronicos", "path": "/para-voce/por-que-vivo/vivo-explica/smartphones-eletronicos", "category": "Vivo Explica"},
    {"slug": "explica-dicionario-velocidade", "path": "/para-voce/por-que-vivo/vivo-explica/internet-e-wi-fi/dicionario-de-velocidade-da-internet", "category": "Vivo Explica"},
    # Por que Vivo
    {"slug": "teste-de-velocidade", "path": "/para-voce/por-que-vivo/qualidade/teste-de-velocidade", "category": "Por que Vivo"},
    {"slug": "premios", "path": "/para-voce/por-que-vivo/qualidade/premios", "category": "Por que Vivo"},
    {"slug": "vivo-renova", "path": "/para-voce/por-que-vivo/beneficios/vivo-renova", "category": "Por que Vivo"},
    {"slug": "vivo-valoriza", "path": "/para-voce/por-que-vivo/vivo-valoriza", "category": "Por que Vivo"},
    # Conteúdos Complementares
    {"slug": "beneficios-vivo-tv", "path": "/para-voce/produtos-e-servicos/para-casa/tv/beneficios-vivo-tv", "category": "Conteúdos Complementares"},
    {"slug": "apps-inclusos-plano-internet", "path": "/para-voce/produtos-e-servicos/servicos-digitais/apps-inclusos-no-plano-de-internet", "category": "Conteúdos Complementares"},
    {"slug": "vivo-smart-wifi", "path": "/para-voce/produtos-e-servicos/para-casa/internet/vivo-smart-wi-fi", "category": "Conteúdos Complementares"},
]

_SLUG_INDEX: dict[str, dict] = {p["slug"]: p for p in PAGE_CATALOG}
ACTIVATION_PAGES = [p["slug"] for p in PAGE_CATALOG if p["category"] == "Ativação de Serviços Digitais"]


def build_url(slug: str) -> str:
    entry = _SLUG_INDEX.get(slug)
    if not entry:
        raise ValueError(f"Slug desconhecido: '{slug}'. Use --list para ver os disponíveis.")
    return f"{BASE_URL}{entry['path']}"

def get_all_slugs() -> list[str]: return [p["slug"] for p in PAGE_CATALOG]
def get_slugs_by_category(category: str) -> list[str]: return [p["slug"] for p in PAGE_CATALOG if category.lower() in p["category"].lower()]
def get_categories() -> list[str]: return list(dict.fromkeys(p["category"] for p in PAGE_CATALOG))
def get_entry(slug: str) -> dict:
    entry = _SLUG_INDEX.get(slug)
    if not entry: raise ValueError(f"Slug desconhecido: '{slug}'")
    return entry

def clean_text(text: str) -> str: return re.sub(r"\s+", " ", text).strip()
def html_to_soup(html: str) -> BeautifulSoup: return BeautifulSoup(html, "html.parser")

def _normalize_href(href: str) -> str:
    if href.startswith("//"): return "https:" + href
    if href.startswith("/"): return BASE_URL + href
    return href

def _inline_links(tag: Tag) -> str:
    def _render(node) -> str:
        if isinstance(node, NavigableString): return str(node)
        if not isinstance(node, Tag): return ""
        if node.name == "a" and node.get("href"):
            href = _normalize_href(node["href"].strip())
            text = "".join(_render(c) for c in node.children)
            return text + (f" Link: {href}" if href and not href.startswith("#") else "")
        return "".join(_render(c) for c in node.children)
    return clean_text(_render(tag))


async def fetch_main_content(page, url: str) -> BeautifulSoup | None:
    try:
        await page.goto(url, wait_until="networkidle", timeout=60_000)
        await page.wait_for_timeout(3000)  # aguarda 3s após networkidle

    except Exception as e:
        print(f"   ⚠️  Timeout/erro ao navegar para {url}: {e}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as e2:
            print(f"   ❌ Falha definitiva: {e2}")
            return None
    rendered_html = await page.content()
    full_soup = html_to_soup(rendered_html)
    main_div = full_soup.find("div", id="main-content") or full_soup.body or full_soup
    return BeautifulSoup(f"<html><head>{full_soup.head or ''}</head><body>{str(main_div)}</body></html>", "html.parser")


def extract_meta(soup: BeautifulSoup) -> dict:
    title = clean_text(soup.title.get_text()) if soup.title else ""
    description = next((m.get("content", "") for m in soup.find_all("meta")
                        if (m.get("name") or m.get("property") or "").lower() == "description"), "")
    return {"title": title, "description": description}


def extract_steps_feature(container: Tag) -> list[str]:
    items = []
    for step_div in container.find_all("div", class_="step"):
        title_tag = step_div.find(class_="step-text-title")
        if not title_tag: continue
        for hidden in title_tag.find_all("span", class_="hide-text"): hidden.decompose()
        title_text = clean_text(title_tag.get_text())
        desc_tag = step_div.find(class_="step-text-description")
        desc_text = _inline_links(desc_tag) if desc_tag else ""
        step_links = []
        btn_div = step_div.find(class_="step-buttons")
        if btn_div:
            for a in btn_div.find_all("a", href=True):
                if "hide-desktop" not in a.get("class", []):
                    href = _normalize_href(a["href"].strip())
                    if href and not href.startswith("#"): step_links.append(href)
        base = " - ".join(filter(None, [title_text, desc_text]))
        seen = set()
        for href in step_links:
            if href not in seen: base += f" Link: {href}"; seen.add(href)
        items.append(base)
    return items


def extract_side_by_side(container: Tag) -> tuple[list[str], bool]:
    items, is_card_layout = [], False
    item_divs = container.find_all("div", class_="side-by-side__item")
    if item_divs:
        for item_div in item_divs:
            title_p = item_div.find("p", class_="side-by-side__title")
            desc_p = item_div.find("p", class_="side-by-side__description")
            if title_p or desc_p:
                parts = [t for t in [_inline_links(title_p) if title_p else "", _inline_links(desc_p) if desc_p else ""] if t]
                if parts: items.append(" - ".join(parts))
            else:
                texts = [_inline_links(p) for p in item_div.find_all("p") if _inline_links(p)]
                items.append(" - ".join(texts) if texts else clean_text(item_div.get_text()))
    else:
        has_content_cards = False
        for card in container.find_all("div", class_="card-text"):
            title_tag = card.find(class_="card-text__title")
            title = clean_text(title_tag.get_text()) if title_tag else ""
            content_div = card.find(class_="card-text__content")
            description = ""
            if content_div:
                paras = content_div.find_all("p")
                description = " ".join(_inline_links(p) for p in paras if _inline_links(p)) if paras else clean_text(content_div.get_text())
            a = next((c for c in card.find_all("a", class_="links-purple", href=True) if not c.find_parent(class_="card-text__content")), None)
            if not a:
                a = next((c for c in card.find_all("a", href=True) if not c.find_parent(class_="card-text__content")), None)
            href, btn_text = "", ""
            if a and a.get("href"):
                candidate = _normalize_href(a["href"].strip())
                if not candidate.startswith("#"): href, btn_text = candidate, clean_text(a.get_text())
            if title and description and href:
                link_part = f" {btn_text} Link: {href}" if btn_text else f" Link: {href}"
                items.append(f"{title}: {description}{link_part}"); has_content_cards = True
            elif title and href: items.append(f"{title} Link: {href}")
            elif title and description: items.append(f"{title}: {description}"); has_content_cards = True
            elif title: items.append(title)
            elif description and href:
                link_part = f" {btn_text} Link: {href}" if btn_text else f" Link: {href}"
                items.append(f"{description}{link_part}")
        if not items:
            items = [_inline_links(p) for p in container.find_all("p") if _inline_links(p)]
        is_card_layout = has_content_cards
    return items, is_card_layout


def extract_accordion_faqs(container: Tag) -> list[dict]:
    faq_items = []
    for li in container.find_all("li", class_="accordion__item"):
        btn = li.find("button", class_="accordion__item__label")
        if not btn: continue
        for span in btn.find_all("span", class_="accordion__item__attach"): span.decompose()
        question = clean_text(btn.get_text())
        content_div = li.find(class_="accordion__item__container")
        faq_items.append({"q": question, "a": _inline_links(content_div) if content_div else ""})
    return faq_items


def _format_faq_answer(container: Tag, faq_index: int) -> str:
    IGNORE_CLASSES = {"slick-slider", "slick-list", "slick-track", "hide-text"}
    lines = []
    def process(node) -> None:
        if isinstance(node, NavigableString): return
        if not isinstance(node, Tag): return
        if set(node.get("class", [])) & IGNORE_CLASSES: return
        if node.name == "p":
            text = _inline_links(node)
            if text: lines.append(text)
        elif node.name == "ol":
            for i, li in enumerate(node.find_all("li", recursive=False), 1):
                text = _inline_links(li)
                if text: lines.append(f"{faq_index}.{i}. {text}")
        elif node.name == "ul":
            for li in node.find_all("li", recursive=False):
                text = _inline_links(li)
                if text: lines.append(f"- {text}")
        else:
            for child in node.children: process(child)
    for child in container.children: process(child)
    buttons_div = container.find("div", class_="accordion__buttons")
    if buttons_div:
        for a in buttons_div.find_all("a", href=True):
            href = _normalize_href(a["href"].strip())
            text = clean_text(a.get_text())
            if text and href and not href.startswith("#"): lines.append(f"{text} Link: {href}")
    return "\n".join(lines)


def extract_accordion_faqs_formatted(container: Tag) -> list[dict]:
    return [{"q": clean_text((lambda btn: [span.decompose() for span in btn.find_all("span", class_="accordion__item__attach")] or btn)(li.find("button", class_="accordion__item__label")).get_text()),
             "a": _format_faq_answer(li.find(class_="accordion__item__container"), i) if li.find(class_="accordion__item__container") else ""}
            for i, li in enumerate(container.find_all("li", class_="accordion__item"), 1)
            if li.find("button", class_="accordion__item__label")]


def collect_all_accordion_faqs(container: Tag) -> list[dict]:
    all_items, index = [], 1
    for ul in container.find_all("ul", class_="accordion"):
        for li in ul.find_all("li", class_="accordion__item"):
            btn = li.find("button", class_="accordion__item__label")
            if not btn: continue
            for span in btn.find_all("span", class_="accordion__item__attach"): span.decompose()
            content_div = li.find(class_="accordion__item__container")
            all_items.append({"q": clean_text(btn.get_text()), "a": _format_faq_answer(content_div, index) if content_div else ""})
            index += 1
    return all_items


def _extract_page_title_section(soup: BeautifulSoup) -> list[dict]:
    h1 = soup.find("h1")
    if not h1:
        return []
    blocks = []
    # Captura p.body que aparece como irmão do h1 dentro do mesmo
    # container (padrão div.title > div.hgroup > div > h1 + p.body)
    parent = h1.parent
    if parent:
        p_body = parent.find("p", class_="body")
        if p_body:
            text = _inline_links(p_body)
            if text:
                blocks.append({"type": "paragraph", "text": text})
    return [{"title": clean_text(h1.get_text()), "blocks": blocks}]

def _extract_steps_from_container(tab_or_section: Tag) -> list[dict]:
    blocks, seen = [], set()
    for sc in [*tab_or_section.find_all("div", attrs={"data-controller": "steps-feature"}),
               *tab_or_section.find_all("div", class_="steps-feature__container")]:
        if id(sc) in seen: continue
        seen.add(id(sc))
        items = extract_steps_feature(sc)
        if items: blocks.append({"type": "ordered", "items": items})
    return blocks


def _extract_richtext_blocks(container: Tag) -> list[dict]:
    blocks = []
    SKIP_CONTAINERS = {"div","section","article","aside","nav","header","footer","main"}
    IGNORE_CLASSES = {"steps-feature__container","steps-feature","accordion","accordion__item","faq-container-component","faq","slick-slider","slick-list","slick-track","hide-text","step-buttons"}
    def should_ignore(node): return bool(set(node.get("class",[])) & IGNORE_CLASSES) or node.get("data-controller") == "steps-feature" or node.get("aria-hidden") == "true"
    def is_block_heading(node):
        if node.name in ("h3","h4"): return True
        if node.name == "p":
            children = [c for c in node.children if not (isinstance(c, NavigableString) and not c.strip())]
            return len(children) == 1 and isinstance(children[0], Tag) and children[0].name == "strong"
        return False
    def walk_richtext(node):
        if not isinstance(node, Tag) or should_ignore(node): return
        if is_block_heading(node):
            text = clean_text(node.get_text())
            if text: blocks.append({"type": "heading", "text": text})
            return
        if node.name == "p":
            text = _inline_links(node)
            if text: blocks.append({"type": "paragraph", "text": text})
            return
        if node.name in ("ul","ol"):
            items = [_inline_links(li) for li in node.find_all("li", recursive=False) if _inline_links(li)]
            if items: blocks.append({"type": "ordered" if node.name == "ol" else "unordered", "items": items})
            return
        if node.name in SKIP_CONTAINERS or node.name == "span":
            for child in node.children:
                if isinstance(child, Tag): walk_richtext(child)
    for child in container.children:
        if isinstance(child, Tag): walk_richtext(child)
    return blocks


def _extract_richtext_full(container: Tag) -> list[dict]:
    blocks = []
    IGNORE_CLASSES = {"slick-slider","slick-list","slick-track","hide-text","accordion","accordion__item","faq-container-component"}
    SKIP_TAGS = {"figure","img","svg","script","style","noscript"}
    def process(node) -> None:
        if isinstance(node, NavigableString):
            text = clean_text(str(node))
            if text: blocks.append({"type": "paragraph", "text": text})
            return
        if not isinstance(node, Tag) or node.name in SKIP_TAGS or set(node.get("class",[])) & IGNORE_CLASSES: return
        if node.name == "p":
            text = _inline_links(node)
            if text: blocks.append({"type": "paragraph", "text": text})
        elif node.name in ("h2","h3","h4"):
            text = clean_text(node.get_text())
            if text: blocks.append({"type": "heading", "text": text})
        elif node.name in ("ul","ol"):
            items = [_inline_links(li) for li in node.find_all("li", recursive=False) if _inline_links(li)]
            list_type = "ordered" if node.name == "ol" else "unordered"
            if items: blocks.append({"type": list_type, "items": items})
        elif node.name == "a" and node.get("href"):
            if "hide-desktop" in node.get("class",[]): return
            href = _normalize_href(node["href"].strip())
            text = clean_text(node.get_text())
            if text and href and not href.startswith("#"): blocks.append({"type": "paragraph", "text": f"{text} Link: {href}"})
        else:
            for child in node.children: process(child)
    for child in container.children: process(child)
    return blocks


def make_faq_duplicate_checker(soup: BeautifulSoup):
    faq_answer_texts = {clean_text(c.get_text()) for c in soup.find_all("div", class_="accordion__item__container") if clean_text(c.get_text())}
    def _is_faq_duplicate(node: Tag) -> bool:
        paras = [clean_text(p.get_text()) for p in node.find_all("p") if clean_text(p.get_text())]
        return bool(paras) and all(any(p in fa or fa in p for fa in faq_answer_texts) for p in paras)
    return _is_faq_duplicate


def append_to_last_section(sections: list[dict], blocks: list[dict]) -> None:
    if not blocks: return
    if sections: sections[-1]["blocks"].extend(blocks)
    else: sections.append({"title": "", "blocks": blocks})


# ── Handlers genéricos ──────────────────────────────────────────────────────

def handle_comunicados(node, sections, is_faq_duplicate, *, use_richtext_full=False):
    if "comunicados" not in node.get("class",[]): return False
    last = sections[-1] if sections else None
    has_waiting = last and last.get("title") and not last.get("blocks")
    if is_faq_duplicate(node) and not has_waiting: return True
    blocks = (_extract_richtext_full if use_richtext_full else _extract_richtext_blocks)(node)
    if blocks: append_to_last_section(sections, blocks)
    return True

def handle_richtext(node, sections):
    if "richtext" not in node.get("class",[]): return False
    if any(node.find_parent("div", class_=c) for c in ("tabs__content-item","accordion__item","teaser","comunicados")): return False
    if node.find_parent("li", class_="accordion__item"): return False
    blocks = _extract_richtext_full(node)
    if blocks: append_to_last_section(sections, blocks)
    return True

def handle_side_by_side_component(node, sections):
    if "side-by-side-component" not in node.get("class",[]): return False
    items, is_card_layout = extract_side_by_side(node)
    if not items: return True
    if is_card_layout:
        blocks = []
        for i, item in enumerate(items):
            if i > 0: blocks.append({"type": "blank"})
            blocks.append({"type": "paragraph", "text": f"- {item}"})
        append_to_last_section(sections, blocks)
    else:
        append_to_last_section(sections, [{"type": "unordered", "items": items}])
    return True

def handle_side_by_side_row(node, sections):
    classes = node.get("class",[])
    if "side-by-side" not in classes or "row" not in classes: return False
    items = [clean_text(h4.get_text()) for h4 in node.find_all("h4", class_="card-text__title") if clean_text(h4.get_text())]
    if items: append_to_last_section(sections, [{"type": "unordered", "items": items}])
    return True

def _extract_card_blocks(card: Tag) -> list[dict]:
    title, description, btn_links = "", "", []
    product = (card if "product-item" in card.get("class",[]) else card.find(class_="product-item"))
    if product:
        title_tag = product.find(class_="product-item__title")
        if title_tag: title = clean_text(title_tag.get_text())
        content_div = product.find(class_="product-item__content")
        if content_div:
            paras = content_div.find_all("p", class_="product-item__text") or content_div.find_all("p")
            description = " ".join(_inline_links(p) for p in paras if _inline_links(p))
        btn_wrapper = product.find(class_="product-item__content-btn")
        anchor_pool = btn_wrapper.find_all("a", href=True) if btn_wrapper else [
            a for a in product.find_all("a", href=True)
            if not any(a.find_parent(class_=c) for c in ("product-item__title","product-item__image","product-item__content"))]
        for a in anchor_pool:
            if "hide-desktop" in a.get("class",[]): continue
            href = _normalize_href(a["href"].strip())
            btn_text = clean_text(a.get("data-label-desktop") or a.get_text())
            if href and not href.startswith("#") and btn_text: btn_links.append(f"{btn_text} Link: {href}")
    else:
        title_tag = card.find(class_="card-text__title")
        if title_tag: title = clean_text(title_tag.get_text())
        content_div = card.find(class_="card-text__content")
        if content_div:
            paras = content_div.find_all("p")
            description = " ".join(_inline_links(p) for p in paras if _inline_links(p)) if paras else clean_text(content_div.get_text())
        btn_wrapper = card.find(class_="card-text__buttons") or card.find(class_="card-text__cta")
        anchor_pool = btn_wrapper.find_all("a", href=True) if btn_wrapper else [
            a for a in card.find_all("a", href=True)
            if not any(a.find_parent(class_=c) for c in ("card-text__title","card-text__image","card-text__content"))]
        for a in anchor_pool:
            if "hide-desktop" in a.get("class",[]): continue
            href = _normalize_href(a["href"].strip())
            btn_text = clean_text(a.get_text())
            if href and not href.startswith("#") and btn_text: btn_links.append(f"{btn_text} Link: {href}")
    return [b for b in [{"type":"paragraph","text":title} if title else None,
                         {"type":"paragraph","text":description} if description else None,
                         *[{"type":"paragraph","text":b} for b in btn_links]] if b]

def handle_slick_cards(node, sections, visited):
    classes = node.get("class",[])
    if ("slick-slider" not in classes and node.get("data-slick") is None) or id(node) in visited: return False
    visited.add(id(node))
    seen_indexes, real_slides = set(), []
    for slide in node.find_all("div", class_="slick-slide"):
        raw = slide.get("data-slick-index")
        if raw is None: continue
        try: idx = int(raw)
        except ValueError: continue
        if idx < 0 or idx in seen_indexes: continue
        seen_indexes.add(idx); real_slides.append(slide)
    real_slides.sort(key=lambda s: int(s.get("data-slick-index",0)))
    card_groups = []
    for slide in real_slides:
        for card in (slide.find_all("div", class_="product-item") or slide.find_all("div", class_="card-text")):
            blocks = _extract_card_blocks(card)
            if blocks: card_groups.append(blocks)
    if not card_groups: return True
    blocks = []
    for i, group in enumerate(card_groups):
        if i > 0: blocks.append({"type": "blank"})
        blocks.extend(group)
    append_to_last_section(sections, blocks)
    return True

def handle_nav_links(node, sections):
    if "nav-links" not in node.get("class",[]): return False
    paragraphs = node.find_all("p")
    blocks = [{"type":"paragraph","text":_inline_links(p)} for p in paragraphs if _inline_links(p)] if paragraphs else ([{"type":"paragraph","text":t}] if (t := _inline_links(node)) else [])
    if blocks: append_to_last_section(sections, blocks)
    return True

def handle_legaltext(node, sections):
    if "legaltext-component" not in node.get("class",[]): return False
    blocks = [{"type":"paragraph","text":_inline_links(p)} for p in node.find_all("p") if _inline_links(p)]
    if blocks: append_to_last_section(sections, blocks)
    return True

def handle_acesso_rapido(node, sections, page_url=""):
    if "acesso-rapido" not in node.get("class",[]): return False
    blocks = []
    for card in node.find_all("a", class_="acesso-rapido__card"):
        raw_href = card.get("href","").strip()
        if not raw_href: continue
        href = (page_url + raw_href) if (raw_href.startswith("#") and page_url) else _normalize_href(raw_href)
        if not href: continue
        title_tag = card.find(class_="acesso-rapido__card-title") or card.find("h2") or card.find("p")
        text = clean_text(title_tag.get_text()) if title_tag else clean_text(card.get_text())
        if text: blocks.append({"type":"paragraph","text":f"{text}\nLink: {href}"})
    if blocks: append_to_last_section(sections, blocks)
    return True

def handle_teaser(node, sections, visited, *, use_richtext_full=False):
    if "teaser" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    title_tag = node.find(class_="teaser__title") or node.find("h2") or node.find("h3")
    if not title_tag:
        if use_richtext_full:
            blocks = _extract_richtext_full(node)
            if blocks: append_to_last_section(sections, blocks)
        return True
    title_text = clean_text(title_tag.get_text()) + "."
    if use_richtext_full:
        title_tag.decompose()
        sections.append({"title": title_text, "blocks": _extract_richtext_full(node)})
    else:
        items = [clean_text(i.get_text()) for i in node.find_all(class_="teaser__icons__text") if clean_text(i.get_text())]
        if items: sections.append({"title": title_text, "blocks": [{"type":"unordered","items":items}]})
    return True

def handle_tabs_component(node, sections, visited, visited_steps):
    if "tabs-component" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    for tab_content in node.find_all("div", class_="tabs__content-item"):
        tab_name = tab_content.get("data-tab-name","")
        if not tab_name: continue
        blocks = list(_extract_steps_from_container(tab_content))
        for sc in [*tab_content.find_all("div", attrs={"data-controller":"steps-feature"}),
                   *tab_content.find_all("div", class_="steps-feature__container")]:
            visited_steps.add(id(sc))
        for acc in tab_content.find_all("ul", class_="accordion"):
            faq_items = extract_accordion_faqs(acc)
            if faq_items: blocks.append({"type":"faq","items":faq_items})
        if not blocks:
            # Extrair side-by-side-component dentro da aba (ex: cards de parceiros)
            for sbs in tab_content.find_all("div", class_="side-by-side-component"):
                from extractors.base import extract_side_by_side
                items, is_card_layout = extract_side_by_side(sbs)
                if items:
                    if is_card_layout:
                        for i, item in enumerate(items):
                            if i > 0:
                                blocks.append({"type": "blank"})
                            blocks.append({"type": "paragraph", "text": f"- {item}"})
                    else:
                        blocks.append({"type": "unordered", "items": items})

        if not blocks:
            blocks.extend(_extract_richtext_blocks(tab_content))
        if blocks: sections.append({"title": tab_name + ".", "blocks": blocks})
    return True

def handle_faq_container(node, sections, visited):
    if "faq-container-component" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    faq_items = collect_all_accordion_faqs(node)
    if faq_items: append_to_last_section(sections, [{"type":"faq","items":faq_items}])
    return True

def handle_accordion_standalone(node, sections, visited):
    if node.name != "ul" or "accordion" not in node.get("class",[]): return False
    if node.find_parent("div", class_="faq-container-component") or id(node) in visited: return False
    visited.add(id(node))
    faq_items = collect_all_accordion_faqs(node)
    if faq_items: append_to_last_section(sections, [{"type":"faq","items":faq_items}])
    return True

HANDLED_COMPONENTS = {"comunicados","richtext","side-by-side-component","side-by-side","tabs-component","steps-feature","faq-container-component","accordion","teaser","slick-slider","see-all-component","cross","nav-links","legaltext-component","end-of-page-component","acesso-rapido","banner-secondary-container-component","online-store-container-component","video-component","container-component","snippet-reference","destaque-banner","photo-text-component","title","list"}

def handle_h2(node, sections, visited, is_faq_duplicate=None):
    if node.name != "h2" or id(node) in visited: return False
    if node.find_parent("div", class_="tabs__content-item") or node.find_parent("div", class_="teaser"): return False
    visited.add(id(node))
    h2_text = clean_text(node.get_text())
    blocks = []
    title_comp = node.find_parent(class_="title")
    if title_comp and is_faq_duplicate is not None:
        sib = title_comp.find_next_sibling()
        while sib and "spacer" in sib.get("class",[]): sib = sib.find_next_sibling()
        is_steps = sib and ("steps-feature" in sib.get("class",[]) or sib.find("div", class_="steps-feature__container") or sib.find("div", attrs={"data-controller":"steps-feature"}))
        is_handled = sib and bool(set(sib.get("class",[])) & HANDLED_COMPONENTS)
        if sib and not is_steps and not is_handled and not is_faq_duplicate(sib):
            blocks = [{"type":"paragraph","text":_inline_links(p)} for p in sib.find_all("p") if _inline_links(p)]
    if not blocks:
        parent = node.parent
        if parent:
            p_body = parent.find("p", class_="body")
            if p_body:
                text = _inline_links(p_body)
                if text:
                    blocks.append({"type": "paragraph", "text": text})
    sections.append({"title": h2_text, "blocks": blocks})
    return True

def handle_h3(node, sections, visited):
    if node.name != "h3" or id(node) in visited: return False
    if node.find_parent("div", class_="tabs__content-item"): return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text: sections.append({"title": text, "blocks": []})
    return True

def handle_p_h2(node, sections, visited):
    if node.name != "p" or "h2" not in node.get("class",[]) or id(node) in visited: return False
    if node.find_parent("div", class_="tabs__content-item"): return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text: sections.append({"title": text + ".", "blocks": []})
    return True

def handle_p_h3(node, sections, visited):
    if node.name != "p" or "h3" not in node.get("class",[]) or id(node) in visited: return False
    if node.find_parent("div", class_="tabs__content-item") or node.find_parent("div", class_="teaser"): return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text: append_to_last_section(sections, [{"type":"heading","text":text}])
    return True

def handle_steps_standalone(node, sections, visited):
    is_steps = node.get("data-controller") == "steps-feature" or "steps-feature__container" in node.get("class",[])
    if not is_steps or id(node) in visited: return False
    if node.find_parent("div", class_="tabs__content-item"): return False
    visited.add(id(node))
    items = extract_steps_feature(node)
    if items:
        last = sections[-1] if sections else None
        if last and last.get("title") and not any(b["type"] == "ordered" for b in last.get("blocks",[])):
            last["blocks"].append({"type":"ordered","items":items})
        else:
            sections.append({"title":"","blocks":[{"type":"ordered","items":items}]})
    return True

def handle_destaque_banner(node, sections, visited):
    if "destaque-banner" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    card_groups = []
    for item in node.find_all("div", class_="destaque-banner__item"):
        link_tag = item.find("a", class_="banner__link")
        if not link_tag or not link_tag.get("href"): continue
        href = _normalize_href(link_tag["href"].strip())
        if not href or href.startswith("#"): continue
        content = item.find("div", class_="destaque-banner__item__content")
        if not content: continue
        overline_tag = content.find("p", class_="overline")
        h3_tag       = content.find("h3") or content.find(class_="h3")  
        btn_span     = content.find("span", class_="h4")
        card_blocks = [b for b in [{"type":"paragraph","text":clean_text(overline_tag.get_text())} if overline_tag else None,
                                    {"type":"paragraph","text":clean_text(h3_tag.get_text())} if h3_tag else None,
                                    {"type":"paragraph","text":f"Link: {href}"}] if b]
        if card_blocks: card_groups.append(card_blocks)
    if not card_groups: return True
    blocks = []
    for i, group in enumerate(card_groups):
        if i > 0: blocks.append({"type":"blank"})
        blocks.extend(group)
    append_to_last_section(sections, blocks)
    return True

def handle_see_all(node, sections, visited):
    if "see-all-component" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    vermais = node.find("div", class_="vermais")
    if not vermais: return True
    title_div, link_div = vermais.find("div", class_="vermais__title"), vermais.find("div", class_="vermais__link")
    title_tag = title_div.find(["h2","h3","p"]) if title_div else None
    title = clean_text(title_tag.get_text()) if title_tag else ""
    href = ""
    if link_div:
        a = link_div.find("a", href=True)
        if a:
            candidate = _normalize_href(a["href"].strip())
            if not candidate.startswith("#"): href = candidate
    if not title: return True
    text = f"{title} Link: {href}" if href else title
    append_to_last_section(sections, [{"type":"paragraph","text":text}])
    return True

def handle_cross(node, sections, visited):
    if "cross" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    card_groups = []
    for card_link in node.find_all("a", class_="cross__item"):
        href = _normalize_href(card_link.get("href","").strip())
        if not href or href.startswith("#"): continue
        content = card_link.find("div", class_="cross__item__content")
        if not content: continue
        overline, h3, btn_span = content.find("p", class_="overline"), content.find("h3"), content.find("span", class_="h4")
        card_blocks = [b for b in [{"type":"paragraph","text":clean_text(overline.get_text())} if overline else None,
                                    {"type":"paragraph","text":clean_text(h3.get_text())} if h3 else None,
                                    {"type":"paragraph","text":f"{clean_text(btn_span.get_text())} Link: {href}"} if btn_span else None] if b]
        if card_blocks: card_groups.append(card_blocks)
    if not card_groups: return True
    blocks = []
    for i, group in enumerate(card_groups):
        if i > 0: blocks.append({"type":"blank"})
        blocks.extend(group)
    append_to_last_section(sections, blocks)
    return True


def handle_banner_secondary(node, sections, visited):
    if "banner-secondary-container-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    def _extract_content_block(content: "Tag") -> list[dict]:
        """Extrai blocos de um div.banner__content."""
        subtitle_tag = (
            content.find("p", class_="overline")
            or content.find("h3", class_="overline")
            or content.find(class_="banner__subtitle")
        )
        title_tag = content.find(class_="banner__title")
        text_tag  = content.find(class_="banner__text")

        # CTAs: links-purple OU links-white OU qualquer <a> dentro de <ul>
        action_links = []
        for a in content.find_all("a", href=True):
            cls = a.get("class", [])
            if "hide-desktop" in cls:
                continue
            # ignora âncoras internas puras
            href = _normalize_href(a["href"].strip())
            if not href or href.startswith("#"):
                continue
            btn_text = clean_text(a.get("data-label-desktop") or a.get_text())
            if btn_text:
                action_links.append(f"{btn_text} Link: {href}")

        return [b for b in [
            {"type": "paragraph", "text": clean_text(subtitle_tag.get_text())} if subtitle_tag else None,
            {"type": "paragraph", "text": clean_text(title_tag.get_text())}    if title_tag  else None,
            {"type": "paragraph", "text": clean_text(text_tag.get_text())}     if text_tag   else None,
            *[{"type": "paragraph", "text": lnk} for lnk in action_links],
        ] if b]

    # ── Variante 1: slick-slider (comportamento original) ──────────────────
    slick = node.find("div", class_="slick-slider")
    if slick:
        seen_indexes, real_slides = set(), []
        for slide in slick.find_all("div", class_="slick-slide"):
            raw = slide.get("data-slick-index")
            if raw is None:
                continue
            try:
                idx = int(raw)
            except ValueError:
                continue
            if idx < 0 or idx in seen_indexes:
                continue
            seen_indexes.add(idx)
            real_slides.append(slide)
        real_slides.sort(key=lambda s: int(s.get("data-slick-index", 0)))

        slide_groups = []
        for slide in real_slides:
            content = slide.find("div", class_="banner__content")
            if content:
                blocks = _extract_content_block(content)
                if blocks:
                    slide_groups.append(blocks)

        if slide_groups:
            blocks = []
            for i, group in enumerate(slide_groups):
                if i > 0:
                    blocks.append({"type": "blank"})
                blocks.extend(group)
            append_to_last_section(sections, blocks)
        return True

    # ── Variante 2: sem slick — slides diretos (banner--secondary__slider) ─
    all_groups = []
    for content in node.find_all("div", class_="banner__content"):
        blocks = _extract_content_block(content)
        if blocks:
            all_groups.append(blocks)

    if all_groups:
        blocks = []
        for i, group in enumerate(all_groups):
            if i > 0:
                blocks.append({"type": "blank"})
            blocks.extend(group)
        append_to_last_section(sections, blocks)

    return True

def handle_highlight_product(node, sections, visited):
    if "highlight-product-component" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    p_h1 = node.find("p", class_="h1")
    if p_h1 and sections: sections[0]["title"] = clean_text(p_h1.get_text())
    for rt in node.find_all("div", class_="richtext"):
        blocks = _extract_richtext_full(rt)
        if blocks: append_to_last_section(sections, blocks)
    return True

def handle_end_of_page(node, sections, visited):
    if "end-of-page-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    for a in node.find_all("a"):
        # Tenta href direto; fallback para data-target
        raw_href = (a.get("href") or a.get("data-target") or "").strip()
        href = _normalize_href(raw_href) if raw_href else ""
        has_valid_href = href and not href.startswith("#")

        text_parts = [clean_text(p.get_text()) for p in a.find_all("p") if clean_text(p.get_text())]
        if not text_parts:
            continue

        if has_valid_href:
            line = " ".join(text_parts) + f" Link: {href}"
        else:
            # Item sem link útil (ex: "Entre em contato → 103 15") - captura só o texto
            line = " ".join(text_parts)

        sections.append({"title": "", "blocks": [{"type": "paragraph", "text": line}]})

    return True

def handle_button_component(node, sections, visited):
    if "button-component" not in node.get("class",[]) or id(node) in visited: return False
    visited.add(id(node))
    for a in node.find_all("a", href=True):
        href = _normalize_href(a["href"].strip())
        text = clean_text(a.get_text())
        if href and not href.startswith("#") and text:
            append_to_last_section(sections, [{"type":"paragraph","text":f"{text} Link: {href}"}])
    return True

def handle_p_standalone(node, sections, extra_protected_parents=()):
    if node.name != "p": return False
    base_protected = ("tabs__content-item","accordion__item","steps-feature__container","teaser","end-of-page-component","comunicados","legaltext-component","nav-links","side-by-side-component","richtext", "online-store-container-component")
    for cls in base_protected + extra_protected_parents:
        if node.find_parent("div", class_=cls) or node.find_parent("li", class_=cls): return False
    if node.get("data-controller") == "steps-feature" or "h2" in node.get("class",[]): return False
    if node.find_parent("div", class_="title") and not node.find_parent("div", class_="teaser__content"): return False
    text = _inline_links(node)
    if text: append_to_last_section(sections, [{"type":"paragraph","text":text}])
    return True


# ── Extratores para CSV ─────────────────────────────────────────────────────

def extract_links(soup: BeautifulSoup) -> list[dict]:
    links, seen = [], set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if href and href not in seen and not href.startswith("#"):
            seen.add(href)
            links.append({"text": clean_text(tag.get_text()) or "(sem texto)", "href": href})
    return links

def extract_tables(soup: BeautifulSoup) -> list[list[list[str]]]:
    tables = []
    for table in soup.find_all("table"):
        rows = [[clean_text(td.get_text()) for td in tr.find_all(["td","th"])] for tr in table.find_all("tr")]
        rows = [r for r in rows if any(r)]
        if rows: tables.append(rows)
    return tables

def flatten_text_blocks(sections: list[dict]) -> list[str]:
    blocks = []
    for section in sections:
        if section.get("title"): blocks.append(section["title"])
        for block in section.get("blocks",[]):
            if block["type"] in ("paragraph","heading"): blocks.append(block["text"])
            elif block["type"] in ("ordered","unordered"): blocks.extend(block["items"])
            elif block["type"] == "faq":
                for faq in block["items"]:
                    blocks.append(faq["q"])
                    if faq["a"]: blocks.append(faq["a"])
    return [b for b in blocks if b]