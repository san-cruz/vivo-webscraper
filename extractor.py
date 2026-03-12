"""
extractor.py — Módulo compartilhado de extração
------------------------------------------------
Contém toda a lógica de:
  - Busca e renderização do HTML via Playwright (apenas o bloco #main-content)
  - Extração de metadados, passos, FAQs, links, tabelas e seções estruturadas
  - Geração de saída .txt (scrapertxt.py) e .csv (scrapercsv.py) importam deste módulo
"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag


# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────

BASE_URL = "https://vivo.com.br"
BASE_PATH = "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais"

# Todas as páginas de ativação conhecidas — slug após ativacao-servicos-digitais/
ACTIVATION_PAGES = [
    "ativacao-apple-music",
    "ativacao-spotify",
    "ativacao-netflix",
    "ativacao-globoplay",
    "ativacao-max",
    "ativacao-amazon-prime",
    "ativacao-telecine",
    "ativacao-premiere",
    "ativacao-youtube-premium",
    "ativacao-vivo-tv",
    "ativacao-vivae",
    "ativacao-vale-saude",
    "ativacao-ip-fixo-digital",
]

# URL da página-índice de ativações (raiz)
INDEX_PAGE = ""   # string vazia = sem slug, usa apenas BASE_PATH


def build_url(slug: str) -> str:
    """Monta a URL completa a partir do slug da página."""
    if slug:
        return f"{BASE_URL}{BASE_PATH}/{slug}"
    return f"{BASE_URL}{BASE_PATH}"


# ──────────────────────────────────────────────
# Helpers de texto
# ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _inline_links(tag: Tag) -> str:
    """
    Reconstrói texto de uma tag inserindo ' Link: <href>' após cada âncora,
    sem duplicar o texto dos filhos.
    """
    def _render(node) -> str:
        if isinstance(node, NavigableString):
            return str(node)
        if not isinstance(node, Tag):
            return ""
        if node.name == "a" and node.get("href"):
            href = node["href"].strip()
            text = "".join(_render(c) for c in node.children)
            suffix = f" Link: {href}" if href and not href.startswith("#") else ""
            return text + suffix
        return "".join(_render(c) for c in node.children)
    return clean_text(_render(tag))


# ──────────────────────────────────────────────
# Busca e renderização via Playwright
# ──────────────────────────────────────────────

async def fetch_main_content(page, url: str) -> BeautifulSoup | None:
    """
    Navega até a URL com Playwright, aguarda o carregamento e retorna
    um BeautifulSoup apenas do bloco <div role="main" id="main-content">.
    Retorna None se o bloco não for encontrado.
    """
    try:
        await page.goto(url, wait_until="networkidle", timeout=60_000)
    except Exception as e:
        print(f"   ⚠️  Timeout/erro ao navegar para {url}: {e}")
        try:
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
        except Exception as e2:
            print(f"   ❌ Falha definitiva: {e2}")
            return None

    rendered_html = await page.content()
    full_soup = html_to_soup(rendered_html)

    # Extrai apenas o bloco principal
    main_div = full_soup.find("div", id="main-content")
    if not main_div:
        # Fallback: body inteiro
        main_div = full_soup.body or full_soup

    # Cria soup isolado com title preservado
    wrapper = BeautifulSoup(
        f"<html><head>{full_soup.head or ''}</head><body>{str(main_div)}</body></html>",
        "html.parser"
    )
    return wrapper


# ──────────────────────────────────────────────
# Extratores de metadados
# ──────────────────────────────────────────────

def extract_meta(soup: BeautifulSoup) -> dict:
    title = clean_text(soup.title.get_text()) if soup.title else ""
    description = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name == "description":
            description = meta.get("content", "")
    return {"title": title, "description": description}


# ──────────────────────────────────────────────
# Extratores especializados para componentes Vivo
# ──────────────────────────────────────────────

def extract_steps_feature(container: Tag) -> list[str]:
    """Extrai passos do componente .steps-feature."""
    items = []
    for step_div in container.find_all("div", class_="step"):
        title_tag = step_div.find(class_="step-text-title")
        if not title_tag:
            continue
        for hidden in title_tag.find_all("span", class_="hide-text"):
            hidden.decompose()
        title_text = clean_text(title_tag.get_text())

        desc_tag = step_div.find(class_="step-text-description")
        desc_text = _inline_links(desc_tag) if desc_tag else ""

        # Coleta links dos botões (ignora versão mobile para evitar duplicação)
        step_links = []
        btn_div = step_div.find(class_="step-buttons")
        if btn_div:
            for a in btn_div.find_all("a", href=True):
                if "hide-desktop" in a.get("class", []):
                    continue
                href = a["href"].strip()
                if href and not href.startswith("#"):
                    step_links.append(href)

        base_parts = [title_text]
        if desc_text:
            base_parts.append(desc_text)
        base = " - ".join(base_parts)

        seen = set()
        for href in step_links:
            if href not in seen:
                base += f" Link: {href}"
                seen.add(href)

        items.append(base)
    return items


def extract_accordion_faqs(container: Tag) -> list[dict]:
    """Extrai FAQs de componentes .accordion."""
    faq_items = []
    for li in container.find_all("li", class_="accordion__item"):
        btn = li.find("button", class_="accordion__item__label")
        if not btn:
            continue
        for span in btn.find_all("span", class_="accordion__item__attach"):
            span.decompose()
        question = clean_text(btn.get_text())
        content_div = li.find(class_="accordion__item__container")
        answer = _inline_links(content_div) if content_div else ""
        faq_items.append({"q": question, "a": answer})
    return faq_items


# ──────────────────────────────────────────────
# Extração de seções estruturadas (ordem DOM)
# ──────────────────────────────────────────────

def _extract_page_title_section(soup: BeautifulSoup) -> list[dict]:
    h1 = soup.find("h1")
    if not h1:
        return []
    return [{"title": clean_text(h1.get_text()), "blocks": []}]


def _extract_steps_from_container(tab_or_section: Tag) -> list[dict]:
    """
    Extrai todos os blocos de passos dentro de um container (aba ou seção avulsa).
    Aceita tanto containers com data-controller="steps-feature" quanto
    containers que usam apenas a classe steps-feature__container (variação
    encontrada em algumas páginas da Vivo, ex: amazon-prime).
    Retorna lista de blocos {"type": "ordered", "items": [...]}.
    """
    blocks = []
    seen_containers: set[int] = set()

    # Estratégia 1: container com data-controller (padrão)
    for sc in tab_or_section.find_all(
        "div", attrs={"data-controller": "steps-feature"}
    ):
        if id(sc) in seen_containers:
            continue
        seen_containers.add(id(sc))
        items = extract_steps_feature(sc)
        if items:
            blocks.append({"type": "ordered", "items": items})

    # Estratégia 2: container sem data-controller mas com a classe
    # steps-feature__container (variante encontrada em amazon-prime e similares)
    for sc in tab_or_section.find_all("div", class_="steps-feature__container"):
        if id(sc) in seen_containers:
            continue
        seen_containers.add(id(sc))
        items = extract_steps_feature(sc)
        if items:
            blocks.append({"type": "ordered", "items": items})

    return blocks


def _extract_richtext_blocks(container: Tag) -> list[dict]:
    """
    Extrai conteúdo de texto rico de um container (aba ou seção):
    - Parágrafos <p> → bloco "paragraph"
    - Subtítulos <h3>/<h4> ou <p> com <strong> como único filho → bloco "heading"
      (formatado no .txt como subtítulo em linha própria)
    - Listas <ul>/<ol> avulsas (fora de steps/accordion) → bloco "unordered"/"ordered"

    Ignora elementos que já são tratados por outros extratores:
    steps-feature, accordion, teaser, slick sliders e elementos ocultos.
    """
    blocks = []

    # Tags de container que devemos descer mas não registrar como bloco
    SKIP_CONTAINERS = {
        "div", "section", "article", "aside", "nav",
        "header", "footer", "main"
    }
    # Classes que indicam elementos a ignorar completamente
    IGNORE_CLASSES = {
        "steps-feature__container", "steps-feature",
        "accordion", "accordion__item",
        "faq-container-component", "faq",          # ignora todo o container de FAQ
        "slick-slider", "slick-list", "slick-track",
        "hide-text", "step-buttons",
    }

    def should_ignore(node: Tag) -> bool:
        node_classes = set(node.get("class", []))
        if node_classes & IGNORE_CLASSES:
            return True
        if node.get("data-controller") == "steps-feature":
            return True
        if node.get("aria-hidden") == "true":
            return True
        return False

    def is_block_heading(node: Tag) -> bool:
        """True se o nó é um subtítulo: <h3>, <h4>, ou <p> com apenas <strong>."""
        if node.name in ("h3", "h4"):
            return True
        if node.name == "p":
            children = [c for c in node.children
                        if not (isinstance(c, NavigableString) and not c.strip())]
            if len(children) == 1 and isinstance(children[0], Tag) \
                    and children[0].name == "strong":
                return True
        return False

    def walk_richtext(node: Tag):
        if not isinstance(node, Tag):
            return
        if should_ignore(node):
            return

        if is_block_heading(node):
            text = clean_text(node.get_text())
            if text:
                blocks.append({"type": "heading", "text": text})
            return

        if node.name == "p":
            text = _inline_links(node)
            if text:
                blocks.append({"type": "paragraph", "text": text})
            return

        if node.name in ("ul", "ol"):
            items = [
                _inline_links(li)
                for li in node.find_all("li", recursive=False)
                if _inline_links(li)
            ]
            if items:
                list_type = "ordered" if node.name == "ol" else "unordered"
                blocks.append({"type": list_type, "items": items})
            return

        if node.name in SKIP_CONTAINERS or node.name in ("span",):
            for child in node.children:
                if isinstance(child, Tag):
                    walk_richtext(child)

    for child in container.children:
        if isinstance(child, Tag):
            walk_richtext(child)

    return blocks


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    """
    Percorre o DOM em ordem e extrai todas as seções:
    título h1, abas de passos/FAQ, teaser de ícones, h2 avulsos,
    steps avulsos (fora de abas) e end-page.
    """
    sections = list(_extract_page_title_section(soup))

    # ── Pré-computa fingerprints de todas as respostas de FAQ da página ──────
    # Qualquer bloco de texto que seja substring de uma resposta de accordion
    # é considerado duplicata mobile e deve ser ignorado quando aparece fora das abas.
    _faq_answer_texts: set[str] = set()
    for container in soup.find_all("div", class_="accordion__item__container"):
        txt = clean_text(container.get_text())
        if txt:
            _faq_answer_texts.add(txt)

    def _is_faq_duplicate(node: Tag) -> bool:
        """True se todos os parágrafos do node são duplicatas de respostas de FAQ."""
        paras = [clean_text(p.get_text()) for p in node.find_all("p") if clean_text(p.get_text())]
        if not paras:
            return False
        return all(
            any(p in faq_ans or faq_ans in p for faq_ans in _faq_answer_texts)
            for p in paras
        )
    # ────────────────────────────────────────────────────────────────────────

    visited_tabs: set[int] = set()
    visited_teasers: set[int] = set()
    visited_h2: set[int] = set()
    visited_end: set[int] = set()
    visited_steps: set[int] = set()

    def _mark_steps_visited(container: Tag) -> None:
        for sc in container.find_all("div", attrs={"data-controller": "steps-feature"}):
            visited_steps.add(id(sc))
        for sc in container.find_all("div", class_="steps-feature__container"):
            visited_steps.add(id(sc))

    def walk(node: Tag):
        if not isinstance(node, Tag):
            return
        classes = node.get("class", [])

        # ── comunicados: ignora se for duplicata mobile de FAQ ───────
        if "comunicados" in classes:
            if _is_faq_duplicate(node):
                return  # descarta sem descer

        # ── tabs-component ──────────────────────────────────────────
        if "tabs-component" in classes and id(node) not in visited_tabs:
            visited_tabs.add(id(node))
            for tab_content in node.find_all("div", class_="tabs__content-item"):
                tab_name = tab_content.get("data-tab-name", "")
                if not tab_name:
                    continue
                blocks = []

                # Passos — usa helper que suporta ambas as variantes do componente
                step_blocks = _extract_steps_from_container(tab_content)
                for sb in step_blocks:
                    blocks.append(sb)
                # Marca os steps desta aba como visitados (evita reprocessar abaixo)
                _mark_steps_visited(tab_content)

                # FAQs
                for acc in tab_content.find_all("ul", class_="accordion"):
                    faq_items = extract_accordion_faqs(acc)
                    if faq_items:
                        blocks.append({"type": "faq", "items": faq_items})

                # Richtext — captura abas com conteúdo somente em texto/parágrafos
                # (ex: "Já sou membro Prime" que tem texto corrido e subtítulos h3/strong)
                if not blocks:
                    blocks.extend(_extract_richtext_blocks(tab_content))

                if blocks:
                    sections.append({"title": tab_name + ".", "blocks": blocks})
            return

        # ── teaser com ícones ───────────────────────────────────────
        if "teaser" in classes and id(node) not in visited_teasers:
            title_tag = node.find(class_="teaser__title")
            if title_tag:
                visited_teasers.add(id(node))
                title = clean_text(title_tag.get_text()) + "."
                items = [
                    clean_text(i.get_text())
                    for i in node.find_all(class_="teaser__icons__text")
                    if clean_text(i.get_text())
                ]
                if items:
                    sections.append({
                        "title": title,
                        "blocks": [{"type": "unordered", "items": items}]
                    })
                return

        # ── h2 avulso (fora de abas e teasers) ─────────────────────
        if node.name == "h2" and id(node) not in visited_h2:
            if not node.find_parent("div", class_="tabs__content-item") and \
               not node.find_parent("div", class_="teaser"):
                visited_h2.add(id(node))
                h2_text = clean_text(node.get_text())
                blocks = []
                title_comp = node.find_parent(class_="title")
                if title_comp:
                    sib = title_comp.find_next_sibling()
                    while sib and "spacer" in sib.get("class", []):
                        sib = sib.find_next_sibling()
                    # Não captura o sibling se for steps (tratado abaixo)
                    # nem se for um comunicados de duplicata mobile de FAQ
                    is_steps = sib and (
                        "steps-feature" in sib.get("class", [])
                        or sib.find("div", class_="steps-feature__container")
                        or sib.find("div", attrs={"data-controller": "steps-feature"})
                    )
                    if sib and not is_steps and not _is_faq_duplicate(sib):
                        for p in sib.find_all("p"):
                            text = _inline_links(p)
                            if text:
                                blocks.append({"type": "paragraph", "text": text})
                sections.append({"title": h2_text, "blocks": blocks})

        # ── <p class="h2"> (ex: "Tire suas dúvidas…") ───────────────
        if node.name == "p" and "h2" in classes and id(node) not in visited_h2:
            if not node.find_parent("div", class_="tabs__content-item"):
                visited_h2.add(id(node))
                text = clean_text(node.get_text())
                if text:
                    sections.append({"title": text + ".", "blocks": []})

        # ── steps-feature avulsos (fora de qualquer aba) ───────────
        # Captura blocos de passos diretamente no DOM, associados a um h2
        # anterior (ex: "Saiba como gerenciar sua cobrança").
        is_steps_container = (
            node.get("data-controller") == "steps-feature"
            or "steps-feature__container" in classes
        )
        if is_steps_container and id(node) not in visited_steps:
            if not node.find_parent("div", class_="tabs__content-item"):
                visited_steps.add(id(node))
                items = extract_steps_feature(node)
                if items:
                    # Tenta anexar ao último h2 registrado (que ainda não tem steps)
                    last = sections[-1] if sections else None
                    if last and last.get("title") and not any(
                        b["type"] == "ordered" for b in last.get("blocks", [])
                    ):
                        last["blocks"].append({"type": "ordered", "items": items})
                    else:
                        sections.append({
                            "title": "",
                            "blocks": [{"type": "ordered", "items": items}]
                        })
                return

        # ── end-of-page ─────────────────────────────────────────────
        if "end-of-page-component" in classes and id(node) not in visited_end:
            visited_end.add(id(node))
            for a in node.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#"):
                    continue
                text_parts = [
                    clean_text(p.get_text()) for p in a.find_all("p")
                    if clean_text(p.get_text())
                ]
                if text_parts:
                    full = " ".join(text_parts) + f" Link: {href}"
                    sections.append({
                        "title": "",
                        "blocks": [{"type": "paragraph", "text": full}]
                    })
            return

        # Desce nos filhos
        for child in node.children:
            if isinstance(child, Tag):
                walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag):
            walk(child)

    return [s for s in sections if s.get("title") or s.get("blocks")]


# ──────────────────────────────────────────────
# Extratores para CSV
# ──────────────────────────────────────────────

def extract_links(soup: BeautifulSoup) -> list[dict]:
    links = []
    seen = set()
    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        text = clean_text(tag.get_text())
        if href and href not in seen and not href.startswith("#"):
            seen.add(href)
            links.append({"text": text or "(sem texto)", "href": href})
    return links


def extract_tables(soup: BeautifulSoup) -> list[list[list[str]]]:
    tables = []
    for table in soup.find_all("table"):
        rows = []
        for tr in table.find_all("tr"):
            cells = [clean_text(td.get_text()) for td in tr.find_all(["td", "th"])]
            if any(cells):
                rows.append(cells)
        if rows:
            tables.append(rows)
    return tables


def flatten_text_blocks(sections: list[dict]) -> list[str]:
    """Achata todas as seções em uma lista de strings de texto."""
    blocks = []
    for section in sections:
        if section.get("title"):
            blocks.append(section["title"])
        for block in section.get("blocks", []):
            if block["type"] in ("paragraph", "heading"):
                blocks.append(block["text"])
            elif block["type"] in ("ordered", "unordered"):
                blocks.extend(block["items"])
            elif block["type"] == "faq":
                for faq in block["items"]:
                    blocks.append(faq["q"])
                    if faq["a"]:
                        blocks.append(faq["a"])
    return [b for b in blocks if b]