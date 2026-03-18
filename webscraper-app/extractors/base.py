"""
extractors/base.py — Módulo base compartilhado
-----------------------------------------------
Contém tudo que é comum a todos os extractors:
  - Catálogo de páginas (PAGE_CATALOG) e funções de consulta
  - Helpers de texto (clean_text, _inline_links, _normalize_href)
  - Busca e renderização via Playwright (fetch_main_content)
  - Extração de metadados (extract_meta)
  - Extratores de componentes Vivo reutilizáveis
  - Handlers genéricos reutilizáveis (handle_*)
  - Extratores para CSV (extract_links, extract_tables, flatten_text_blocks)

Cada extractor especializado importa deste módulo e implementa
sua própria função extract_sections().
"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag


# ──────────────────────────────────────────────
# Catálogo de páginas
# ──────────────────────────────────────────────

BASE_URL = "https://vivo.com.br"

PAGE_CATALOG: list[dict] = [

    # ── Ativação de Serviços Digitais ──────────────────────────────────────
    {
        "slug": "ativacao-amazon-prime",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-amazon-prime",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-apple-music",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-apple-music",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-disney-plus",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-disney-plus",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-globoplay",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-globoplay",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-max",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-max",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-netflix",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-netflix",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-premiere",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-premiere",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-spotify",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-spotify",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-telecine",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-telecine",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-vivo-play",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-vivo-play",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-vivae",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-vivae",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-vale-saude",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-vale-saude",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-mcafee",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-mcafee",
        "category": "Ativação de Serviços Digitais",
    },
    {
        "slug": "ativacao-ip-fixo-digital",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-ip-fixo-digital",
        "category": "Ativação de Serviços Digitais",
    },

    # ── Ajuda e Autoatendimento ────────────────────────────────────────────
    {
        "slug": "app-vivo",
        "path": "/para-voce/app-vivo",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "mais-ajuda",
        "path": "/para-voce/ajuda/mais-ajuda",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "encontre-uma-loja",
        "path": "/para-voce/ajuda/mais-ajuda/encontre-uma-loja",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "dicas-wifi",
        "path": "/para-voce/ajuda/autoatendimento/dicas-wifi",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "mudanca-de-endereco",
        "path": "/para-voce/ajuda/autoatendimento/mudanca-de-endereco",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "servico-de-instalacao",
        "path": "/para-voce/ajuda/autoatendimento/servico-de-instalacao",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "portabilidade",
        "path": "/para-voce/ajuda/sou-novo-aqui/portabilidade",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "ativando-o-chip",
        "path": "/para-voce/ajuda/sou-novo-aqui/ativando-o-chip",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "consumo-de-internet",
        "path": "/para-voce/ajuda/sou-novo-aqui/consumo-de-internet",
        "category": "Ajuda e Autoatendimento",
    },

    # ── Fatura ─────────────────────────────────────────────────────────────
    {
        "slug": "2-via-de-fatura",
        "path": "/para-voce/ajuda/minha-fatura/2-via-de-fatura",
        "category": "Fatura",
    },
    {
        "slug": "entenda-sua-fatura",
        "path": "/para-voce/ajuda/minha-fatura/entenda-sua-fatura",
        "category": "Fatura",
    },
    {
        "slug": "fatura-digital",
        "path": "/para-voce/ajuda/minha-fatura/fatura-digital",
        "category": "Fatura",
    },
    {
        "slug": "debito-automatico",
        "path": "/para-voce/ajuda/minha-fatura/debito-automatico",
        "category": "Fatura",
    },
    {
        "slug": "negociacao-de-debitos",
        "path": "/para-voce/ajuda/minha-fatura/negociacao-de-debitos",
        "category": "Fatura",
    },
    {
        "slug": "pagamento",
        "path": "/para-voce/ajuda/minha-fatura/pagamento",
        "category": "Fatura",
    },
    {
        "slug": "bloqueio-de-linha",
        "path": "/para-voce/ajuda/minha-fatura/bloqueio-de-linha",
        "category": "Fatura",
    },

    # ── Dúvidas — Internet ─────────────────────────────────────────────────
    {
        "slug": "duvidas-internet-wifi",
        "path": "/para-voce/ajuda/duvidas/internet/internet-vivo-wi-fi",
        "category": "Dúvidas — Internet",
    },
    {
        "slug": "duvidas-internet-fibra",
        "path": "/para-voce/ajuda/duvidas/internet/internet-fibra",
        "category": "Dúvidas — Internet",
    },
    {
        "slug": "duvidas-internet-vivo-total",
        "path": "/para-voce/ajuda/duvidas/internet/internet-vivo-total",
        "category": "Dúvidas — Internet",
    },

    # ── Dúvidas — TV ──────────────────────────────────────────────────────
    {
        "slug": "duvidas-tv-fibra",
        "path": "/para-voce/ajuda/duvidas/tv/tv-fibra",
        "category": "Dúvidas — TV",
    },
    {
        "slug": "duvidas-tv-apps-canais",
        "path": "/para-voce/ajuda/duvidas/tv/tv-apps-de-canais",
        "category": "Dúvidas — TV",
    },
    {
        "slug": "duvidas-tv-assinatura",
        "path": "/para-voce/ajuda/duvidas/tv/tv-assinatura",
        "category": "Dúvidas — TV",
    },
    {
        "slug": "duvidas-tv-online",
        "path": "/para-voce/ajuda/duvidas/tv/tv-online",
        "category": "Dúvidas — TV",
    },

    # ── Vivo Explica ───────────────────────────────────────────────────────
    {
        "slug": "explica-internet-wifi",
        "path": "/para-voce/por-que-vivo/vivo-explica/internet-e-wi-fi",
        "category": "Vivo Explica",
    },
    {
        "slug": "explica-smartphones-eletronicos",
        "path": "/para-voce/por-que-vivo/vivo-explica/smartphones-eletronicos",
        "category": "Vivo Explica",
    },
    {
        "slug": "explica-dicionario-velocidade",
        "path": "/para-voce/por-que-vivo/vivo-explica/internet-e-wi-fi/dicionario-de-velocidade-da-internet",
        "category": "Vivo Explica",
    },

    # ── Por que Vivo ───────────────────────────────────────────────────────
    {
        "slug": "teste-de-velocidade",
        "path": "/para-voce/por-que-vivo/qualidade/teste-de-velocidade",
        "category": "Por que Vivo",
    },
    {
        "slug": "premios",
        "path": "/para-voce/por-que-vivo/qualidade/premios",
        "category": "Por que Vivo",
    },
    {
        "slug": "vivo-renova",
        "path": "/para-voce/por-que-vivo/beneficios/vivo-renova",
        "category": "Por que Vivo",
    },
    {
        "slug": "vivo-valoriza",
        "path": "/para-voce/por-que-vivo/vivo-valoriza",
        "category": "Por que Vivo",
    },

    # ── Conteúdos Complementares ───────────────────────────────────────────
    {
        "slug": "beneficios-vivo-tv",
        "path": "/para-voce/produtos-e-servicos/para-casa/tv/beneficios-vivo-tv",
        "category": "Conteúdos Complementares",
    },
    {
        "slug": "apps-inclusos-plano-internet",
        "path": "/para-voce/produtos-e-servicos/servicos-digitais/apps-inclusos-no-plano-de-internet",
        "category": "Conteúdos Complementares",
    },
    {
        "slug": "vivo-smart-wifi",
        "path": "/para-voce/produtos-e-servicos/para-casa/internet/vivo-smart-wi-fi",
        "category": "Conteúdos Complementares",
    },
]

_SLUG_INDEX: dict[str, dict] = {p["slug"]: p for p in PAGE_CATALOG}

# Compatibilidade com scrapercsv.py
ACTIVATION_PAGES = [
    p["slug"] for p in PAGE_CATALOG
    if p["category"] == "Ativação de Serviços Digitais"
]


def build_url(slug: str) -> str:
    entry = _SLUG_INDEX.get(slug)
    if not entry:
        raise ValueError(f"Slug desconhecido: '{slug}'. Use --list para ver os disponíveis.")
    return f"{BASE_URL}{entry['path']}"


def get_all_slugs() -> list[str]:
    return [p["slug"] for p in PAGE_CATALOG]


def get_slugs_by_category(category: str) -> list[str]:
    cat_lower = category.lower()
    return [p["slug"] for p in PAGE_CATALOG if cat_lower in p["category"].lower()]


def get_categories() -> list[str]:
    seen = []
    for p in PAGE_CATALOG:
        if p["category"] not in seen:
            seen.append(p["category"])
    return seen


def get_entry(slug: str) -> dict:
    entry = _SLUG_INDEX.get(slug)
    if not entry:
        raise ValueError(f"Slug desconhecido: '{slug}'")
    return entry


# ──────────────────────────────────────────────
# Helpers de texto
# ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def html_to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


def _normalize_href(href: str) -> str:
    """
    Converte href para URL absoluta com esquema https.
      /path           → https://vivo.com.br/path
      //domain/path   → https://domain/path   (protocol-relative)
      http://...      → mantém
      https://...     → mantém
      #anchor         → mantém
    """
    if href.startswith("//"):
        return "https:" + href
    if href.startswith("/"):
        return BASE_URL + href
    return href


def _inline_links(tag: Tag) -> str:
    """Reconstrói texto de uma tag inserindo ' Link: <href>' após cada âncora."""
    def _render(node) -> str:
        if isinstance(node, NavigableString):
            return str(node)
        if not isinstance(node, Tag):
            return ""
        if node.name == "a" and node.get("href"):
            href = _normalize_href(node["href"].strip())
            text = "".join(_render(c) for c in node.children)
            suffix = f" Link: {href}" if href and not href.startswith("#") else ""
            return text + suffix
        return "".join(_render(c) for c in node.children)
    return clean_text(_render(tag))


# ──────────────────────────────────────────────
# Busca e renderização via Playwright
# ──────────────────────────────────────────────

async def fetch_main_content(page, url: str) -> BeautifulSoup | None:
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

    main_div = full_soup.find("div", id="main-content")
    if not main_div:
        main_div = full_soup.body or full_soup

    wrapper = BeautifulSoup(
        f"<html><head>{full_soup.head or ''}</head><body>{str(main_div)}</body></html>",
        "html.parser"
    )
    return wrapper


# ──────────────────────────────────────────────
# Extração de metadados
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
# Extratores de componentes Vivo (compartilhados)
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
        step_links = []
        btn_div = step_div.find(class_="step-buttons")
        if btn_div:
            for a in btn_div.find_all("a", href=True):
                if "hide-desktop" in a.get("class", []):
                    continue
                href = _normalize_href(a["href"].strip())
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


def extract_side_by_side(container: Tag) -> tuple[list[str], bool]:
    """
    Extrai itens do componente .side-by-side-component.

    Retorna (items, is_card_layout) onde:
    - items: lista de strings extraídas
    - is_card_layout: True quando os items são cards com título + conteúdo
      (variante 4), que devem ser renderizados como paragraphs separados por
      blank no output. False para listas simples (unordered).

    Suporta cinco variantes, avaliadas em ordem:
    1. side-by-side__item > p.side-by-side__title + p.side-by-side__description
    2. side-by-side__item > <p> simples
    3. div.card-text > (h4|p).card-text__title + a.links-purple ou a[href]
       → "Título Link: href"
    4. div.card-text > (h4|p).card-text__title + div.card-text__content (sem link)
       → "Título: Descrição"  (is_card_layout=True)
    5. Fallback: qualquer <p> dentro do componente
    """
    items = []
    is_card_layout = False

    item_divs = container.find_all("div", class_="side-by-side__item")
    if item_divs:
        for item_div in item_divs:
            title_p = item_div.find("p", class_="side-by-side__title")
            desc_p  = item_div.find("p", class_="side-by-side__description")
            if title_p or desc_p:
                parts = []
                if title_p:
                    t = _inline_links(title_p)
                    if t:
                        parts.append(t)
                if desc_p:
                    d = _inline_links(desc_p)
                    if d:
                        parts.append(d)
                if parts:
                    items.append(" - ".join(parts))
            else:
                texts = [_inline_links(p) for p in item_div.find_all("p") if _inline_links(p)]
                if texts:
                    items.append(" - ".join(texts))
                else:
                    t = clean_text(item_div.get_text())
                    if t:
                        items.append(t)
    else:
        has_content_cards = False  # rastreia se usamos variante 4
        for card in container.find_all("div", class_="card-text"):
            # Título: aceita h4 OU p com a classe card-text__title
            title_tag = card.find(class_="card-text__title")
            title = clean_text(title_tag.get_text()) if title_tag else ""

            # Descrição: dentro de card-text__content
            content_div = card.find(class_="card-text__content")
            description = ""
            if content_div:
                paras = content_div.find_all("p")
                if paras:
                    description = " ".join(
                        _inline_links(p) for p in paras if _inline_links(p)
                    )
                else:
                    description = clean_text(content_div.get_text())

            # Link: procura links-purple fora do content, depois qualquer <a> fora do content
            # (âncoras dentro de card-text__content já são capturadas via _inline_links acima)
            a = None
            for candidate_a in card.find_all("a", class_="links-purple", href=True):
                if not candidate_a.find_parent(class_="card-text__content"):
                    a = candidate_a
                    break
            if not a:
                for candidate_a in card.find_all("a", href=True):
                    if not candidate_a.find_parent(class_="card-text__content"):
                        a = candidate_a
                        break
            href = ""
            btn_text = ""
            if a and a.get("href"):
                candidate = _normalize_href(a["href"].strip())
                if not candidate.startswith("#"):
                    href = candidate
                    btn_text = clean_text(a.get_text())

            if title and description and href:
                # Variante 3b: título + descrição + link externo
                # "Título: Descrição link_text Link: href"
                link_part = f" {btn_text} Link: {href}" if btn_text else f" Link: {href}"
                items.append(f"{title}: {description}{link_part}")
                has_content_cards = True
            elif title and href:
                # Variante 3: título + link (sem descrição)
                items.append(f"{title} Link: {href}")
            elif title and description:
                # Variante 4: título + descrição (sem link) → card layout
                items.append(f"{title}: {description}")
                has_content_cards = True
            elif title:
                items.append(title)

        if not items:
            # Fallback: qualquer <p> dentro do componente
            for p in container.find_all("p"):
                text = _inline_links(p)
                if text:
                    items.append(text)

        is_card_layout = has_content_cards

    return items, is_card_layout


def extract_accordion_faqs(container: Tag) -> list[dict]:
    """Extrai FAQs de ul.accordion (resposta como string inline)."""
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


def _format_faq_answer(container: Tag, faq_index: int) -> str:
    """
    Formata o conteúdo de accordion__item__container preservando estrutura:
      ol > li  → N.1. texto, N.2. texto  (N = índice 1-based do FAQ)
      ul > li  → - texto
      p        → texto simples
    """
    IGNORE_CLASSES = {"slick-slider", "slick-list", "slick-track", "hide-text"}
    lines = []

    def process(node) -> None:
        if isinstance(node, NavigableString):
            return
        if not isinstance(node, Tag):
            return
        if set(node.get("class", [])) & IGNORE_CLASSES:
            return
        if node.name == "p":
            text = _inline_links(node)
            if text:
                lines.append(text)
        elif node.name == "ol":
            for i, li in enumerate(node.find_all("li", recursive=False), 1):
                text = _inline_links(li)
                if text:
                    lines.append(f"{faq_index}.{i}. {text}")
        elif node.name == "ul":
            for li in node.find_all("li", recursive=False):
                text = _inline_links(li)
                if text:
                    lines.append(f"- {text}")
        else:
            for child in node.children:
                process(child)

    for child in container.children:
        process(child)

    buttons_div = container.find("div", class_="accordion__buttons")
    if buttons_div:
        for a in buttons_div.find_all("a", href=True):
            href = _normalize_href(a["href"].strip())
            text = clean_text(a.get_text())
            if text and href and not href.startswith("#"):
                lines.append(f"{text} Link: {href}")

    return "\n".join(lines)


def extract_accordion_faqs_formatted(container: Tag) -> list[dict]:
    """
    Variante de extract_accordion_faqs que formata a resposta preservando
    listas numeradas (N.1, N.2) e não-numeradas (- item).
    """
    faq_items = []
    for i, li in enumerate(container.find_all("li", class_="accordion__item"), 1):
        btn = li.find("button", class_="accordion__item__label")
        if not btn:
            continue
        for span in btn.find_all("span", class_="accordion__item__attach"):
            span.decompose()
        question = clean_text(btn.get_text())
        content_div = li.find(class_="accordion__item__container")
        answer = _format_faq_answer(content_div, i) if content_div else ""
        faq_items.append({"q": question, "a": answer})
    return faq_items


def collect_all_accordion_faqs(container: Tag) -> list[dict]:
    """
    Coleta todos os ul.accordion dentro de um container e agrupa
    seus itens em uma única lista de FAQs com numeração contínua.
    """
    all_items = []
    index = 1
    for ul in container.find_all("ul", class_="accordion"):
        for li in ul.find_all("li", class_="accordion__item"):
            btn = li.find("button", class_="accordion__item__label")
            if not btn:
                continue
            for span in btn.find_all("span", class_="accordion__item__attach"):
                span.decompose()
            question = clean_text(btn.get_text())
            content_div = li.find(class_="accordion__item__container")
            answer = _format_faq_answer(content_div, index) if content_div else ""
            all_items.append({"q": question, "a": answer})
            index += 1
    return all_items


def _extract_page_title_section(soup: BeautifulSoup) -> list[dict]:
    """Retorna seção inicial com o título h1 da página."""
    h1 = soup.find("h1")
    if not h1:
        return []
    return [{"title": clean_text(h1.get_text()), "blocks": []}]


def _extract_steps_from_container(tab_or_section: Tag) -> list[dict]:
    """Extrai todos os blocos de passos de um container (aba ou seção avulsa)."""
    blocks = []
    seen_containers: set[int] = set()
    for sc in tab_or_section.find_all("div", attrs={"data-controller": "steps-feature"}):
        if id(sc) in seen_containers:
            continue
        seen_containers.add(id(sc))
        items = extract_steps_feature(sc)
        if items:
            blocks.append({"type": "ordered", "items": items})
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
    p, h3/h4, ul/ol. Ignora componentes estruturados (steps, accordion, slick).
    """
    blocks = []
    SKIP_CONTAINERS = {
        "div", "section", "article", "aside", "nav",
        "header", "footer", "main"
    }
    IGNORE_CLASSES = {
        "steps-feature__container", "steps-feature",
        "accordion", "accordion__item",
        "faq-container-component", "faq",
        "slick-slider", "slick-list", "slick-track",
        "hide-text", "step-buttons",
    }

    def should_ignore(node: Tag) -> bool:
        if set(node.get("class", [])) & IGNORE_CLASSES:
            return True
        if node.get("data-controller") == "steps-feature":
            return True
        if node.get("aria-hidden") == "true":
            return True
        return False

    def is_block_heading(node: Tag) -> bool:
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


def _extract_richtext_full(container: Tag) -> list[dict]:
    """
    Versão estendida de _extract_richtext_blocks que também processa:
    - h2/h3/h4 como headings
    - a.btn ou <a> direta como paragraph com link
    - NavigableString direta no container (ex: div.richtext.body sem <p> wrapper)
    Usada por extractors que precisam de extração mais completa (duvidas, ajuda).
    """
    blocks: list[dict] = []
    IGNORE_CLASSES = {
        "slick-slider", "slick-list", "slick-track",
        "hide-text", "accordion", "accordion__item",
        "faq-container-component",
    }
    SKIP_TAGS = {"figure", "img", "svg", "script", "style", "noscript"}

    def process(node) -> None:
        if isinstance(node, NavigableString):
            # Captura texto direto no container (sem wrapper <p>)
            # Ocorre em div.richtext.body onde o texto é filho imediato
            text = clean_text(str(node))
            if text:
                blocks.append({"type": "paragraph", "text": text})
            return
        if not isinstance(node, Tag):
            return
        if node.name in SKIP_TAGS:
            return
        if set(node.get("class", [])) & IGNORE_CLASSES:
            return
        if node.name == "p":
            text = _inline_links(node)
            if text:
                blocks.append({"type": "paragraph", "text": text})
            return
        if node.name in ("h2", "h3", "h4"):
            text = clean_text(node.get_text())
            if text:
                blocks.append({"type": "heading", "text": text})
            return
        if node.name == "ul":
            items = [
                _inline_links(li)
                for li in node.find_all("li", recursive=False)
                if _inline_links(li)
            ]
            if items:
                blocks.append({"type": "unordered", "items": items})
            return
        if node.name == "ol":
            items = [
                _inline_links(li)
                for li in node.find_all("li", recursive=False)
                if _inline_links(li)
            ]
            if items:
                blocks.append({"type": "ordered", "items": items})
            return
        if node.name == "a" and node.get("href"):
            # Ignora a versão mobile (hide-desktop) de botões duplicados.
            # Botões de app store têm duas versões no HTML: hide-mobile (desktop)
            # e hide-desktop (mobile). Capturamos apenas a versão desktop.
            if "hide-desktop" in node.get("class", []):
                return
            href = _normalize_href(node["href"].strip())
            text = clean_text(node.get_text())
            if text and href and not href.startswith("#"):
                blocks.append({"type": "paragraph", "text": f"{text} Link: {href}"})
            return
        for child in node.children:
            process(child)

    for child in container.children:
        process(child)

    return blocks


# ──────────────────────────────────────────────
# Helpers de estado para extractors
# ──────────────────────────────────────────────

def make_faq_duplicate_checker(soup: BeautifulSoup):
    """
    Retorna uma função _is_faq_duplicate(node) que detecta se um node
    contém apenas texto que já aparece em respostas de accordion.

    Usada para evitar duplicação de conteúdo mobile/desktop nos extractors
    de ativação e similares.
    """
    faq_answer_texts: set[str] = set()
    for container in soup.find_all("div", class_="accordion__item__container"):
        txt = clean_text(container.get_text())
        if txt:
            faq_answer_texts.add(txt)

    def _is_faq_duplicate(node: Tag) -> bool:
        paras = [clean_text(p.get_text()) for p in node.find_all("p") if clean_text(p.get_text())]
        if not paras:
            return False
        return all(
            any(p in faq_ans or faq_ans in p for faq_ans in faq_answer_texts)
            for p in paras
        )

    return _is_faq_duplicate


def append_to_last_section(sections: list[dict], blocks: list[dict]) -> None:
    """
    Anexa blocos à última seção da lista. Se não houver seções, cria uma nova.
    Padrão comum a todos os extractors.
    """
    if not blocks:
        return
    last = sections[-1] if sections else None
    if last is not None:
        last["blocks"].extend(blocks)
    else:
        sections.append({"title": "", "blocks": blocks})


# ──────────────────────────────────────────────
# Handlers genéricos reutilizáveis
# ──────────────────────────────────────────────
# Cada handle_* recebe (node, sections, visited_*) e retorna True se processou,
# False se o node não é do tipo esperado ou já foi visitado.
# Os extractors chamam esses handlers em seu walk() para evitar duplicação.

def handle_comunicados(
    node: Tag,
    sections: list[dict],
    is_faq_duplicate,
    *,
    use_richtext_full: bool = False,
) -> bool:
    """
    Processa div.comunicados.
    - use_richtext_full=True usa _extract_richtext_full (mais completo, para duvidas/ajuda)
    - use_richtext_full=False usa _extract_richtext_blocks (para ativacao)
    """
    if "comunicados" not in node.get("class", []):
        return False
    last = sections[-1] if sections else None
    has_waiting_section = (
        last is not None
        and last.get("title")
        and not last.get("blocks")
    )
    if is_faq_duplicate(node) and not has_waiting_section:
        return True
    fn = _extract_richtext_full if use_richtext_full else _extract_richtext_blocks
    rich_blocks = fn(node)
    if rich_blocks:
        append_to_last_section(sections, rich_blocks)
    return True


def handle_richtext(node: Tag, sections: list[dict]) -> bool:
    """Processa div.richtext com _extract_richtext_full."""
    if "richtext" not in node.get("class", []):
        return False
    if (node.find_parent("div", class_="tabs__content-item")
            or node.find_parent("li", class_="accordion__item")
            or node.find_parent("div", class_="teaser")
            or node.find_parent("div", class_="comunicados")):
        return False
    blocks = _extract_richtext_full(node)
    if blocks:
        append_to_last_section(sections, blocks)
    return True


def handle_side_by_side_component(node: Tag, sections: list[dict]) -> bool:
    """
    Processa div.side-by-side-component.

    Quando is_card_layout=True (cards com título + conteúdo sem link, ex: SMS cards),
    cada item é emitido como paragraph separado por blank — mesmo layout dos slick_cards.
    Nos demais casos emite como bloco unordered.
    """
    if "side-by-side-component" not in node.get("class", []):
        return False
    items, is_card_layout = extract_side_by_side(node)
    if not items:
        return True

    if is_card_layout:
        # Cada item vira um paragraph, separados por blank entre si
        blocks: list[dict] = []
        for i, item in enumerate(items):
            if i > 0:
                blocks.append({"type": "blank"})
            blocks.append({"type": "paragraph", "text": f"- {item}"})
        append_to_last_section(sections, blocks)
    else:
        append_to_last_section(sections, [{"type": "unordered", "items": items}])
    return True


def handle_side_by_side_row(node: Tag, sections: list[dict]) -> bool:
    """Processa div.row.side-by-side (cards com h4.card-text__title)."""
    classes = node.get("class", [])
    if "side-by-side" not in classes or "row" not in classes:
        return False
    items = [
        clean_text(h4.get_text())
        for h4 in node.find_all("h4", class_="card-text__title")
        if clean_text(h4.get_text())
    ]
    if items:
        append_to_last_section(sections, [{"type": "unordered", "items": items}])
    return True


def _extract_card_blocks(card: Tag) -> list[dict]:
    """
    Extrai blocos de um card individual de carrossel Slick.

    Suporta duas variantes de estrutura usadas pelo site Vivo:

    Variante A — card-text (usado em duvidas, vivo-explica, etc.):
      div.card-text
        (h4|p).card-text__title        ← título
        div.card-text__content > p     ← descrição
        div.card-text__buttons > a     ← botão  (ou card-text__cta, ou <a> direto)

    Variante B — product-item (usado em app-vivo, mais-ajuda, etc.):
      div.product-item
        div.product-item__content-wrapper
          (h2|h3|p).product-item__title     ← título
          div.product-item__content > p.product-item__text  ← descrição
          div.product-item__content-btn > a.product-item__link  ← botão
    """
    title = ""
    description = ""
    btn_links: list[str] = []

    # ── Detecta variante B: product-item ───────────────────────────────────
    product = (
        card if "product-item" in card.get("class", [])
        else card.find(class_="product-item")
    )
    if product:
        # Título
        title_tag = product.find(class_="product-item__title")
        if title_tag:
            title = clean_text(title_tag.get_text())

        # Descrição
        content_div = product.find(class_="product-item__content")
        if content_div:
            paras = content_div.find_all("p", class_="product-item__text")
            if not paras:
                paras = content_div.find_all("p")
            description = " ".join(
                _inline_links(p) for p in paras if _inline_links(p)
            )

        # Botão: procura em product-item__content-btn, depois fallback
        btn_wrapper = product.find(class_="product-item__content-btn")
        if btn_wrapper:
            anchor_pool = btn_wrapper.find_all("a", href=True)
        else:
            anchor_pool = [
                a for a in product.find_all("a", href=True)
                if not a.find_parent(class_="product-item__title")
                and not a.find_parent(class_="product-item__image")
                and not a.find_parent(class_="product-item__content")
            ]
        for a in anchor_pool:
            if "hide-desktop" in a.get("class", []):
                continue
            href = _normalize_href(a["href"].strip())
            # Usa data-label-desktop quando disponível (texto canônico do botão)
            btn_text = a.get("data-label-desktop") or clean_text(a.get_text())
            btn_text = clean_text(btn_text)
            if href and not href.startswith("#") and btn_text:
                btn_links.append(f"{btn_text} Link: {href}")

    # ── Variante A: card-text ───────────────────────────────────────────────
    else:
        # Título
        title_tag = card.find(class_="card-text__title")
        if title_tag:
            title = clean_text(title_tag.get_text())

        # Descrição
        content_div = card.find(class_="card-text__content")
        if content_div:
            paras = content_div.find_all("p")
            if paras:
                description = " ".join(
                    _inline_links(p) for p in paras if _inline_links(p)
                )
            else:
                description = clean_text(content_div.get_text())

        # Botão
        btn_wrapper = (
            card.find(class_="card-text__buttons")
            or card.find(class_="card-text__cta")
        )
        if btn_wrapper:
            anchor_pool = btn_wrapper.find_all("a", href=True)
        else:
            anchor_pool = [
                a for a in card.find_all("a", href=True)
                if not a.find_parent(class_="card-text__title")
                and not a.find_parent(class_="card-text__image")
                and not a.find_parent(class_="card-text__content")
            ]
        for a in anchor_pool:
            if "hide-desktop" in a.get("class", []):
                continue
            href = _normalize_href(a["href"].strip())
            btn_text = clean_text(a.get_text())
            if href and not href.startswith("#") and btn_text:
                btn_links.append(f"{btn_text} Link: {href}")

    blocks: list[dict] = []
    if title:
        blocks.append({"type": "paragraph", "text": title})
    if description:
        blocks.append({"type": "paragraph", "text": description})
    for btn in btn_links:
        blocks.append({"type": "paragraph", "text": btn})
    return blocks


def handle_slick_cards(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa carrosséis Slick (div.slick-slider) que contêm cards estruturados.

    Suporta dois tipos de card usados pelo site Vivo:
      - div.card-text    (duvidas, vivo-explica, side-by-side)
      - div.product-item (app-vivo, mais-ajuda, slider-products)

    Estratégia anti-duplicata baseada em data-slick-index:
      O Slick em modo "infinite" insere clones com data-slick-index NEGATIVO
      antes do primeiro slide e clones com index >= N após o último.
      Os slides reais têm sempre data-slick-index >= 0 e únicos.
      Filtrar por index >= 0 e desduplicar por valor de index garante
      exatamente um card por posição, independente de aria-hidden.

    Cada card gera blocos paragraph separados por um bloco "blank" (linha vazia).
    """
    classes = node.get("class", [])
    is_slick = "slick-slider" in classes or node.get("data-slick") is not None
    if not is_slick or id(node) in visited:
        return False
    visited.add(id(node))

    # Coleta slides reais: data-slick-index >= 0, sem repetição de index
    seen_indexes: set[int] = set()
    real_slides: list[Tag] = []
    for slide in node.find_all("div", class_="slick-slide"):
        raw_index = slide.get("data-slick-index")
        if raw_index is None:
            continue
        try:
            idx = int(raw_index)
        except ValueError:
            continue
        if idx < 0 or idx in seen_indexes:
            continue  # clone do infinite scroll
        seen_indexes.add(idx)
        real_slides.append(slide)

    # Ordena por index para garantir ordem correta
    real_slides.sort(key=lambda s: int(s.get("data-slick-index", 0)))

    card_groups: list[list[dict]] = []
    for slide in real_slides:
        # Detecta o tipo de card presente no slide
        card_tags = (
            slide.find_all("div", class_="product-item")
            or slide.find_all("div", class_="card-text")
        )
        for card in card_tags:
            blocks = _extract_card_blocks(card)
            if blocks:
                card_groups.append(blocks)

    if not card_groups:
        return True  # slick sem cards reconhecidos — marca como visitado e segue

    # Intercala grupos com separador de linha em branco
    blocks: list[dict] = []
    for i, group in enumerate(card_groups):
        if i > 0:
            blocks.append({"type": "blank"})
        blocks.extend(group)

    append_to_last_section(sections, blocks)
    return True


def handle_nav_links(node: Tag, sections: list[dict]) -> bool:
    """Processa div.nav-links (texto + link de documento/termos)."""
    if "nav-links" not in node.get("class", []):
        return False
    para_blocks = []
    paragraphs = node.find_all("p")
    if paragraphs:
        for p in paragraphs:
            text = _inline_links(p)
            if text:
                para_blocks.append({"type": "paragraph", "text": text})
    else:
        text = _inline_links(node)
        if text:
            para_blocks.append({"type": "paragraph", "text": text})
    if para_blocks:
        append_to_last_section(sections, para_blocks)
    return True


def handle_legaltext(node: Tag, sections: list[dict]) -> bool:
    """Processa div.legaltext-component (rodapé legal)."""
    if "legaltext-component" not in node.get("class", []):
        return False
    para_blocks = []
    for p in node.find_all("p"):
        text = _inline_links(p)
        if text:
            para_blocks.append({"type": "paragraph", "text": text})
    if para_blocks:
        append_to_last_section(sections, para_blocks)
    return True


def handle_acesso_rapido(
    node: Tag,
    sections: list[dict],
    page_url: str = "",
) -> bool:
    """
    Processa div.acesso-rapido (cards de navegação).
    Estrutura: div.acesso-rapido > ... > a.acesso-rapido__card > (h2|p)

    page_url: URL completa da página atual (ex: "https://vivo.com.br/para-voce/...").
    Quando fornecida, links âncora (#secao) são resolvidos para URL completa:
    "#cobertura" + page_url → "https://vivo.com.br/para-voce/...dicas-wifi#cobertura"
    """
    if "acesso-rapido" not in node.get("class", []):
        return False
    blocks = []
    for card in node.find_all("a", class_="acesso-rapido__card"):
        raw_href = card.get("href", "").strip()
        if not raw_href:
            continue

        # Resolve âncoras usando a URL da página quando disponível
        if raw_href.startswith("#") and page_url:
            href = page_url + raw_href
        else:
            href = _normalize_href(raw_href)
            if not href:
                continue

        # Título: h2.acesso-rapido__card-title, h2 genérico, ou <p>
        title_tag = (
            card.find(class_="acesso-rapido__card-title")
            or card.find("h2")
            or card.find("p")
        )
        text = clean_text(title_tag.get_text()) if title_tag else clean_text(card.get_text())
        if text:
            blocks.append({"type": "paragraph", "text": f"{text}\nLink: {href}"})
    if blocks:
        append_to_last_section(sections, blocks)
    return True


def handle_teaser(
    node: Tag,
    sections: list[dict],
    visited: set[int],
    *,
    use_richtext_full: bool = False,
) -> bool:
    """
    Processa div.teaser.
    - use_richtext_full=False (padrão): extrai apenas teaser__icons__text como unordered
    - use_richtext_full=True: extrai conteúdo completo após remover o título
    """
    if "teaser" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    title_tag = (
        node.find(class_="teaser__title")
        or node.find("h2")
        or node.find("h3")
    )
    if not title_tag:
        if use_richtext_full:
            blocks = _extract_richtext_full(node)
            if blocks:
                append_to_last_section(sections, blocks)
        return True

    title_text = clean_text(title_tag.get_text()) + "."

    if use_richtext_full:
        title_tag.decompose()
        blocks = _extract_richtext_full(node)
        sections.append({"title": title_text, "blocks": blocks})
    else:
        items = [
            clean_text(i.get_text())
            for i in node.find_all(class_="teaser__icons__text")
            if clean_text(i.get_text())
        ]
        if items:
            sections.append({
                "title": title_text,
                "blocks": [{"type": "unordered", "items": items}]
            })

    return True


def handle_tabs_component(
    node: Tag,
    sections: list[dict],
    visited: set[int],
    visited_steps: set[int],
) -> bool:
    """Processa div.tabs-component (abas com passos e/ou FAQs)."""
    if "tabs-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    for tab_content in node.find_all("div", class_="tabs__content-item"):
        tab_name = tab_content.get("data-tab-name", "")
        if not tab_name:
            continue
        blocks = []
        step_blocks = _extract_steps_from_container(tab_content)
        blocks.extend(step_blocks)
        # Marca steps dentro da aba como visitados
        for sc in tab_content.find_all("div", attrs={"data-controller": "steps-feature"}):
            visited_steps.add(id(sc))
        for sc in tab_content.find_all("div", class_="steps-feature__container"):
            visited_steps.add(id(sc))
        for acc in tab_content.find_all("ul", class_="accordion"):
            faq_items = extract_accordion_faqs(acc)
            if faq_items:
                blocks.append({"type": "faq", "items": faq_items})
        if not blocks:
            blocks.extend(_extract_richtext_blocks(tab_content))
        if blocks:
            sections.append({"title": tab_name + ".", "blocks": blocks})
    return True


def handle_faq_container(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """Processa div.faq-container-component (bloco de FAQs agrupados)."""
    if "faq-container-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))
    faq_items = collect_all_accordion_faqs(node)
    if faq_items:
        append_to_last_section(sections, [{"type": "faq", "items": faq_items}])
    return True


def handle_accordion_standalone(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """Processa ul.accordion avulso (fora de faq-container-component)."""
    if node.name != "ul" or "accordion" not in node.get("class", []):
        return False
    if node.find_parent("div", class_="faq-container-component"):
        return False
    if id(node) in visited:
        return False
    visited.add(id(node))
    faq_items = collect_all_accordion_faqs(node)
    if faq_items:
        append_to_last_section(sections, [{"type": "faq", "items": faq_items}])
    return True


def handle_h2(
    node: Tag,
    sections: list[dict],
    visited: set[int],
    is_faq_duplicate=None,
) -> bool:
    """Processa <h2> avulso fora de tabs/teaser."""
    if node.name != "h2" or id(node) in visited:
        return False
    if (node.find_parent("div", class_="tabs__content-item")
            or node.find_parent("div", class_="teaser")):
        return False
    visited.add(id(node))
    h2_text = clean_text(node.get_text())
    blocks = []
    title_comp = node.find_parent(class_="title")
    if title_comp and is_faq_duplicate is not None:
        sib = title_comp.find_next_sibling()
        while sib and "spacer" in sib.get("class", []):
            sib = sib.find_next_sibling()
        # Classes de componentes que têm handlers próprios no walk().
        # Quando o sibling imediato é um desses componentes, NÃO pré-carregamos
        # seu conteúdo aqui: o walk() os processará separadamente e pré-carregá-los
        # causaria duplicação.
        HANDLED_COMPONENTS = {
            "comunicados", "richtext",
            "side-by-side-component", "side-by-side",
            "tabs-component", "steps-feature",
            "faq-container-component", "accordion",
            "teaser", "slick-slider",
            "see-all-component", "cross",
            "nav-links", "legaltext-component",
            "end-of-page-component", "acesso-rapido",
            "banner-secondary-container-component",
            "online-store-container-component",
            "video-component", "container-component",
            "snippet-reference", "destaque-banner",
            "photo-text-component",
            "title",
            "list"
        }
        is_steps = sib and (
            "steps-feature" in sib.get("class", [])
            or sib.find("div", class_="steps-feature__container")
            or sib.find("div", attrs={"data-controller": "steps-feature"})
        )
        is_handled = sib and bool(
            set(sib.get("class", [])) & HANDLED_COMPONENTS
        )
        if sib and not is_steps and not is_handled and not is_faq_duplicate(sib):
            for p in sib.find_all("p"):
                text = _inline_links(p)
                if text:
                    blocks.append({"type": "paragraph", "text": text})
    sections.append({"title": h2_text, "blocks": blocks})
    return True


def handle_h3(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    """Processa <h3> avulso fora de tabs."""
    if node.name != "h3" or id(node) in visited:
        return False
    if node.find_parent("div", class_="tabs__content-item"):
        return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text:
        sections.append({"title": text, "blocks": []})
    return True


def handle_p_h2(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    """Processa <p class="h2"> avulso fora de tabs."""
    if node.name != "p" or "h2" not in node.get("class", []):
        return False
    if node.find_parent("div", class_="tabs__content-item"):
        return False
    if id(node) in visited:
        return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text:
        sections.append({"title": text + ".", "blocks": []})
    return True


def handle_p_h3(node: Tag, sections: list[dict], visited: set[int]) -> bool:
    """
    Processa <p class="h3"> dentro de div.title — subtítulo de subseção.

    Usado em páginas como consumo-de-internet onde cada categoria
    ("Vídeos Online", "Música", "Mapas", "Notificações") é um
    <p class="h3"> dentro de div.title, seguido por div.comunicados
    com o parágrafo explicativo.

    Gera um bloco {"type": "heading"} na seção atual, para que o
    comunicados seguinte adicione seu parágrafo à mesma seção.
    No scrapertxt.py: heading renderiza como linha simples ("Vídeos Online\n")
    seguida do parágrafo e blank — idêntico ao formato esperado.
    """
    if node.name != "p" or "h3" not in node.get("class", []):
        return False
    if node.find_parent("div", class_="tabs__content-item"):
        return False
    if node.find_parent("div", class_="teaser"):
        return False
    if id(node) in visited:
        return False
    visited.add(id(node))
    text = clean_text(node.get_text())
    if text:
        append_to_last_section(sections, [{"type": "heading", "text": text}])
    return True


def handle_steps_standalone(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """Processa steps-feature avulsos (fora de tabs)."""
    is_steps_container = (
        node.get("data-controller") == "steps-feature"
        or "steps-feature__container" in node.get("class", [])
    )
    if not is_steps_container or id(node) in visited:
        return False
    if node.find_parent("div", class_="tabs__content-item"):
        return False
    visited.add(id(node))
    items = extract_steps_feature(node)
    if items:
        last = sections[-1] if sections else None
        if last and last.get("title") and not any(
            b["type"] == "ordered" for b in last.get("blocks", [])
        ):
            last["blocks"].append({"type": "ordered", "items": items})
        else:
            sections.append({"title": "", "blocks": [{"type": "ordered", "items": items}]})
    return True


def handle_destaque_banner(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.destaque-banner (componente de banners de destaque com planos/produtos).

    Estrutura HTML (consumo-de-internet — planos Vivo Pós, Controle, etc.):
      div.destaque-banner[data-controller="highlights"]
        div.container > div.row
          div.destaque-banner__item
            a.banner__link[href]         ← link do plano
              div.destaque-banner__item__background  ← imagem (ignorada)
              div.destaque-banner__item__content
                p.overline               ← nome do plano (ex: "Vivo Pós")
                h3.h3                    ← descrição (ex: "O plano Pós com seu app favorito")

    Cada item gera um grupo de paragraphs: overline + h3 + "Link: href",
    separados por blank entre items.
    """
    if "destaque-banner" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    card_groups: list[list[dict]] = []

    for item in node.find_all("div", class_="destaque-banner__item"):
        link_tag = item.find("a", class_="banner__link")
        if not link_tag or not link_tag.get("href"):
            continue
        href = _normalize_href(link_tag["href"].strip())
        if not href or href.startswith("#"):
            continue

        content = item.find("div", class_="destaque-banner__item__content")
        if not content:
            continue

        overline_tag = content.find("p", class_="overline")
        h3_tag = content.find("h3")

        overline = clean_text(overline_tag.get_text()) if overline_tag else ""
        h3_text  = clean_text(h3_tag.get_text()) if h3_tag else ""

        card_blocks: list[dict] = []
        if overline:
            card_blocks.append({"type": "paragraph", "text": overline})
        if h3_text:
            card_blocks.append({"type": "paragraph", "text": h3_text})
        card_blocks.append({"type": "paragraph", "text": f"Link: {href}"})

        if card_blocks:
            card_groups.append(card_blocks)

    if not card_groups:
        return True

    blocks: list[dict] = []
    for i, group in enumerate(card_groups):
        if i > 0:
            blocks.append({"type": "blank"})
        blocks.extend(group)

    append_to_last_section(sections, blocks)
    return True


def handle_see_all(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.see-all-component (componente "Ver mais" / "Vivo Explica").

    Estrutura HTML:
      div.see-all-component
        div.container > div.vermais
          div.vermais__title > h2   ← título da seção (ex: "Vivo Explica: ...")
          div.vermais__link > a     ← link de ação (ex: "Conheça")

    Gera um paragraph com: "Título Link: href"
    O link de ação é incorporado ao título para que o leitor saiba onde ir.
    """
    if "see-all-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    vermais = node.find("div", class_="vermais")
    if not vermais:
        return True

    title_div = vermais.find("div", class_="vermais__title")
    link_div  = vermais.find("div", class_="vermais__link")

    title_tag = title_div.find(["h2", "h3", "p"]) if title_div else None
    title = clean_text(title_tag.get_text()) if title_tag else ""

    href = ""
    if link_div:
        a = link_div.find("a", href=True)
        if a:
            candidate = _normalize_href(a["href"].strip())
            if not candidate.startswith("#"):
                href = candidate

    if not title:
        return True

    if href:
        text = f"{title} Link: {href}"
    else:
        text = title

    append_to_last_section(sections, [{"type": "paragraph", "text": text}])
    return True


def handle_cross(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.cross (componente cross-sell com cards de navegação).

    Estrutura HTML:
      div.cross
        div.col-xl-6
          a.cross__item[href]          ← link envolve tudo
            div.cross__item__content
              p.overline               ← categoria / eyebrow (ex: "Vivo Dúvidas")
              h3                       ← descrição do card
              span.h4                  ← texto do botão (ex: "Conferir dúvidas")

    Cada card gera três blocos paragraph:
      overline
      h3
      "texto_botão Link: href"
    separados por um blank entre cards.
    """
    if "cross" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))

    card_groups: list[list[dict]] = []

    for card_link in node.find_all("a", class_="cross__item"):
        href = _normalize_href(card_link.get("href", "").strip())
        if not href or href.startswith("#"):
            continue

        content = card_link.find("div", class_="cross__item__content")
        if not content:
            continue

        overline = content.find("p", class_="overline")
        h3 = content.find("h3")
        btn_span = content.find("span", class_="h4")

        overline_text = clean_text(overline.get_text()) if overline else ""
        h3_text = clean_text(h3.get_text()) if h3 else ""
        btn_text = clean_text(btn_span.get_text()) if btn_span else ""

        card_blocks: list[dict] = []
        if overline_text:
            card_blocks.append({"type": "paragraph", "text": overline_text})
        if h3_text:
            card_blocks.append({"type": "paragraph", "text": h3_text})
        if btn_text:
            card_blocks.append({"type": "paragraph", "text": f"{btn_text} Link: {href}"})

        if card_blocks:
            card_groups.append(card_blocks)

    if not card_groups:
        return True

    blocks: list[dict] = []
    for i, group in enumerate(card_groups):
        if i > 0:
            blocks.append({"type": "blank"})
        blocks.extend(group)

    append_to_last_section(sections, blocks)
    return True


def handle_banner_secondary(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.banner-secondary-container-component (carrossel de banners).

    Estrutura HTML:
      div.banner-secondary-container-component
        div.banner--secondary__slider.slick-slider
          div.slick-list > div.slick-track
            div.slick-slide[data-slick-index="N"]
              div.banner--secondary
                div.banner__inner
                  div.banner__content
                    p.overline / h3.overline  → eyebrow (ex: "Agendamento App Vivo")
                    (p|h2).banner__title       → título principal
                    p.banner__text             → descrição (pode estar vazia)
                    ul > li > a.links-purple   → link de ação

    Regra de deduplicação: igual ao handle_slick_cards — data-slick-index >= 0,
    sem repetição de index (clones do infinite scroll têm index negativo).
    Todos os slides reais são extraídos, mesmo os com aria-hidden="true".

    Cada slide gera um grupo de paragraphs. Grupos separados por blank.
    Links de ação com class="hide-mobile" são preferidos; links com
    class="hide-desktop" são ignorados para evitar duplicação.
    """
    if "banner-secondary-container-component" not in node.get("class", []) \
            or id(node) in visited:
        return False
    visited.add(id(node))

    slick = node.find("div", class_="slick-slider")
    if not slick:
        return True

    # Coleta slides reais por data-slick-index (>= 0, sem repetição)
    seen_indexes: set[int] = set()
    real_slides: list[Tag] = []
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

    slide_groups: list[list[dict]] = []

    for slide in real_slides:
        content = slide.find("div", class_="banner__content")
        if not content:
            continue

        # Subtitle / eyebrow: p.overline, h3.overline, p.banner__subtitle, ou h3.banner__subtitle
        subtitle_tag = (
            content.find("p", class_="overline")
            or content.find("h3", class_="overline")
            or content.find(class_="banner__subtitle")
        )
        subtitle = clean_text(subtitle_tag.get_text()) if subtitle_tag else ""

        # Título: qualquer tag com classe banner__title
        title_tag = content.find(class_="banner__title")
        title = clean_text(title_tag.get_text()) if title_tag else ""

        # Descrição: p.banner__text (pode estar vazio)
        text_tag = content.find(class_="banner__text")
        text = clean_text(text_tag.get_text()) if text_tag else ""

        # Link de ação: dentro de ul > li > a.links-purple
        # Ignora links com classe hide-desktop (versão mobile duplicada)
        action_links: list[str] = []
        for a in content.find_all("a", class_="links-purple", href=True):
            if "hide-desktop" in a.get("class", []):
                continue
            href = _normalize_href(a["href"].strip())
            if not href or href.startswith("#"):
                continue
            btn_text = clean_text(a.get_text())
            if btn_text:
                action_links.append(f"{btn_text} Link: {href}")

        slide_blocks: list[dict] = []
        if subtitle:
            slide_blocks.append({"type": "paragraph", "text": subtitle})
        if title:
            slide_blocks.append({"type": "paragraph", "text": title})
        if text:
            slide_blocks.append({"type": "paragraph", "text": text})
        for link in action_links:
            slide_blocks.append({"type": "paragraph", "text": link})

        if slide_blocks:
            slide_groups.append(slide_blocks)

    if not slide_groups:
        return True

    blocks: list[dict] = []
    for i, group in enumerate(slide_groups):
        if i > 0:
            blocks.append({"type": "blank"})
        blocks.extend(group)

    append_to_last_section(sections, blocks)
    return True


def handle_highlight_product(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """
    Processa div.highlight-product-component (banner hero de páginas de ajuda).

    Estrutura HTML (mudanca-de-endereco, servico-de-instalacao):
      div.highlight-product-component.secondary-components
        div.banner[data-controller="highlightproduct"]
          div.banner__top  ← imagem de fundo (ignorada)
          div.container
            div.row
              div.col-xl-8.richtext__underline
                h1.overline     ← eyebrow/label (ex: "MUDANÇA DE ENDEREÇO")
                                   capturado por _extract_page_title_section mas
                                   NÃO é o título semântico da página
                p.h1            ← título real da página
                                   (ex: "A Vivo acompanha você até sua nova casa")
                div.richtext.body ← texto descritivo abaixo do título

    Comportamento:
    - Se p.h1 existe: atualiza o título da primeira seção (que foi criada com
      h1.overline pelo _extract_page_title_section) para o texto do p.h1,
      que é o título semântico real da página.
    - Captura div.richtext.body e adiciona como parágrafo da mesma seção.
    """
    if "highlight-product-component" not in node.get("class", []) \
            or id(node) in visited:
        return False
    visited.add(id(node))

    # p.h1 é o título semântico real — substitui o h1.overline (eyebrow)
    p_h1 = node.find("p", class_="h1")
    if p_h1:
        real_title = clean_text(p_h1.get_text())
        if real_title and sections:
            # Atualiza o título da primeira seção criada por _extract_page_title_section
            sections[0]["title"] = real_title

    # Extrai texto descritivo do div.richtext.body
    for rt in node.find_all("div", class_="richtext"):
        blocks = _extract_richtext_full(rt)
        if blocks:
            append_to_last_section(sections, blocks)

    return True


def handle_end_of_page(
    node: Tag,
    sections: list[dict],
    visited: set[int],
) -> bool:
    """Processa div.end-of-page-component."""
    if "end-of-page-component" not in node.get("class", []) or id(node) in visited:
        return False
    visited.add(id(node))
    for a in node.find_all("a", href=True):
        href = _normalize_href(a["href"].strip())
        if href.startswith("#"):
            continue
        text_parts = [
            clean_text(p.get_text()) for p in a.find_all("p")
            if clean_text(p.get_text())
        ]
        if text_parts:
            full = " ".join(text_parts) + f" Link: {href}"
            sections.append({"title": "", "blocks": [{"type": "paragraph", "text": full}]})
    return True


def handle_p_standalone(
    node: Tag,
    sections: list[dict],
    extra_protected_parents: tuple[str, ...] = (),
) -> bool:
    """
    Processa <p> avulso que não está dentro de nenhum container protegido.
    extra_protected_parents: classes de divs adicionais a ignorar (por extractor).
    """
    if node.name != "p":
        return False
    base_protected = (
        "tabs__content-item",
        "accordion__item",
        "steps-feature__container",
        "teaser",
        "end-of-page-component",
        "comunicados",
        "legaltext-component",
        "nav-links",
        "side-by-side-component",
        "richtext",
    )
    all_protected = base_protected + extra_protected_parents
    for cls in all_protected:
        if node.find_parent("div", class_=cls) or node.find_parent("li", class_=cls):
            return False
    if node.get("data-controller") == "steps-feature":
        return False
    if "h2" in node.get("class", []):
        return False
    # Ignora <p> que está dentro de div.title — esses parágrafos descritivos
    # (ex: <p class="body">Leve em consideração...</p>) fazem parte do
    # componente de título AEM e seriam duplicados porque o conteúdo da seção
    # já é tratado pelos handlers do sibling seguinte.
    if node.find_parent("div", class_="title") and \
            not node.find_parent("div", class_="teaser__content"):
        return False
    text = _inline_links(node)
    if text:
        append_to_last_section(sections, [{"type": "paragraph", "text": text}])
    return True


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