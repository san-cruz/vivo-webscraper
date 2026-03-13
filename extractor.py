"""
extractor.py — Módulo compartilhado de extração
------------------------------------------------
Contém toda a lógica de:
  - Busca e renderização do HTML via Playwright (apenas o bloco #main-content)
  - Extração de metadados, passos, FAQs, links, tabelas e seções estruturadas
  - Geração de saída .txt (scrapertxt.py) e .csv (scrapercsv.py) importam deste módulo

Regra de seleção de páginas:
  Apenas páginas informativas e estáticas são incluídas — sem seções de
  valores de produtos, pacotes ou planos comerciais.
"""

import re
from bs4 import BeautifulSoup, NavigableString, Tag


# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────

BASE_URL = "https://vivo.com.br"

# ---------------------------------------------------------------------------
# Catálogo de páginas válidas para geração de TXT
#
# Cada entrada é um dict com:
#   slug     → identificador único usado como nome do arquivo de saída
#   url      → URL completa da página (sem BASE_URL quando relativa, ou absoluta)
#   category → agrupamento lógico (usado em --list e relatórios)
#
# Regra de inclusão:
#   ✅ Páginas informativas / estáticas: tutoriais, ajuda, dúvidas, explica
#   ❌ Excluídas: páginas com vitrine de planos, preços ou seleção de produtos
# ---------------------------------------------------------------------------

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

    # ── Ajuda — Autoatendimento ────────────────────────────────────────────
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
        "slug": "ativando-o-chip",
        "path": "/para-voce/ajuda/sou-novo-aqui/ativando-o-chip",
        "category": "Ajuda e Autoatendimento",
    },
    {
        "slug": "consumo-de-internet",
        "path": "/para-voce/ajuda/sou-novo-aqui/consumo-de-internet",
        "category": "Ajuda e Autoatendimento",
    },

    # ── Ajuda — Fatura ─────────────────────────────────────────────────────
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

    # ── Conteúdos Complementares de Produtos ──────────────────────────────
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

# Índice rápido: slug → entry
_SLUG_INDEX: dict[str, dict] = {p["slug"]: p for p in PAGE_CATALOG}

# Mantido para compatibilidade com scrapercsv.py legado
ACTIVATION_PAGES = [
    p["slug"] for p in PAGE_CATALOG
    if p["category"] == "Ativação de Serviços Digitais"
]


def build_url(slug: str) -> str:
    """Retorna a URL completa dado um slug do catálogo."""
    entry = _SLUG_INDEX.get(slug)
    if not entry:
        raise ValueError(f"Slug desconhecido: '{slug}'. Use --list para ver os disponíveis.")
    return f"{BASE_URL}{entry['path']}"


def get_all_slugs() -> list[str]:
    """Retorna todos os slugs do catálogo, na ordem de definição."""
    return [p["slug"] for p in PAGE_CATALOG]


def get_slugs_by_category(category: str) -> list[str]:
    """Retorna slugs filtrados por categoria (case-insensitive, substring)."""
    cat_lower = category.lower()
    return [p["slug"] for p in PAGE_CATALOG if cat_lower in p["category"].lower()]


def get_categories() -> list[str]:
    """Retorna lista de categorias únicas, na ordem em que aparecem no catálogo."""
    seen = []
    for p in PAGE_CATALOG:
        if p["category"] not in seen:
            seen.append(p["category"])
    return seen


def get_entry(slug: str) -> dict:
    """Retorna o dict completo de uma entrada do catálogo."""
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


def extract_side_by_side(container: Tag) -> list[str]:
    """
    Extrai itens do componente .side-by-side-component como lista unordered.

    Suporta três variantes encontradas nas páginas Vivo:
    1. p.side-by-side__title + p.side-by-side__description → 'Título - Descrição'
    2. div.side-by-side__item > <p> simples → texto do parágrafo
    3. Fallback: qualquer <p> direto dentro do componente (sem wrapper __item)
    """
    items = []
    item_divs = container.find_all("div", class_="side-by-side__item")
    if item_divs:
        for item_div in item_divs:
            title_p = item_div.find("p", class_="side-by-side__title")
            desc_p  = item_div.find("p", class_="side-by-side__description")
            if title_p or desc_p:
                # Variante 1: classes semânticas
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
                # Variante 2: <p> simples dentro do item
                texts = [_inline_links(p) for p in item_div.find_all("p") if _inline_links(p)]
                if texts:
                    items.append(" - ".join(texts))
                else:
                    # Variante 2b: texto direto no item (sem <p>)
                    t = clean_text(item_div.get_text())
                    if t:
                        items.append(t)
    else:
        # Variante 3: sem __item wrappers — tenta h4.card-text__title (componente card real da Vivo)
        h4_items = [
            clean_text(h4.get_text())
            for h4 in container.find_all("h4", class_="card-text__title")
            if clean_text(h4.get_text())
        ]
        if h4_items:
            items.extend(h4_items)
        else:
            # Variante 4: fallback — qualquer <p> dentro do componente
            for p in container.find_all("p"):
                text = _inline_links(p)
                if text:
                    items.append(text)
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
    - Listas <ul>/<ol> avulsas (fora de steps/accordion) → bloco "unordered"/"ordered"
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
        node_classes = set(node.get("class", []))
        if node_classes & IGNORE_CLASSES:
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


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    """
    Percorre o DOM em ordem e extrai todas as seções:
    título h1, abas de passos/FAQ, teaser de ícones, h2 avulsos,
    steps avulsos (fora de abas) e end-page.
    """
    sections = list(_extract_page_title_section(soup))

    _faq_answer_texts: set[str] = set()
    for container in soup.find_all("div", class_="accordion__item__container"):
        txt = clean_text(container.get_text())
        if txt:
            _faq_answer_texts.add(txt)

    def _is_faq_duplicate(node: Tag) -> bool:
        paras = [clean_text(p.get_text()) for p in node.find_all("p") if clean_text(p.get_text())]
        if not paras:
            return False
        return all(
            any(p in faq_ans or faq_ans in p for faq_ans in _faq_answer_texts)
            for p in paras
        )

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

        if "comunicados" in classes:
            # Descarta apenas se for duplicata mobile de FAQ E não houver seção-título
            # esperando conteúdo. Quando um p.h2 ("Sobre mudanças...") já foi registrado
            # como última seção sem blocos, o comunicados é sempre seu conteúdo —
            # independente de o texto coincidir com respostas de FAQ de outras abas
            # (comportamento confirmado em ativacao-disney-plus).
            last = sections[-1] if sections else None
            has_waiting_section = (
                last is not None
                and last.get("title")
                and not last.get("blocks")
            )
            if _is_faq_duplicate(node) and not has_waiting_section:
                return
            # Usa _extract_richtext_blocks para capturar toda a estrutura interna:
            # ul > li > strong (bullets de subtítulo), <p> e <ul> intercalados.
            rich_blocks = _extract_richtext_blocks(node)
            if rich_blocks:
                if last is not None:
                    last["blocks"].extend(rich_blocks)
                else:
                    sections.append({"title": "", "blocks": rich_blocks})
            return

        # ── side-by-side-component ──────────────────────────────────
        if "side-by-side-component" in classes:
            items = extract_side_by_side(node)
            if items:
                last = sections[-1] if sections else None
                if last is not None:
                    last["blocks"].append({"type": "unordered", "items": items})
                else:
                    sections.append({"title": "", "blocks": [{"type": "unordered", "items": items}]})
            return

        # ── side-by-side (cards com ícone + h4.card-text__title) ────
        # Estrutura: div.row.side-by-side > div.card-text > h4.card-text__title
        if "side-by-side" in classes and "row" in classes:
            items = [
                clean_text(h4.get_text())
                for h4 in node.find_all("h4", class_="card-text__title")
                if clean_text(h4.get_text())
            ]
            if items:
                last = sections[-1] if sections else None
                if last is not None:
                    last["blocks"].append({"type": "unordered", "items": items})
                else:
                    sections.append({"title": "", "blocks": [{"type": "unordered", "items": items}]})
            return

        # ── nav-links (texto + link de documento) ──────────────────
        # Suporta: <p>texto <a href>...</p>, <a href> direto, ou texto+link inline
        if "nav-links" in classes:
            para_blocks = []
            paragraphs = node.find_all("p")
            if paragraphs:
                # Variante com <p>
                for p in paragraphs:
                    text = _inline_links(p)
                    if text:
                        para_blocks.append({"type": "paragraph", "text": text})
            else:
                # Variante sem <p>: captura links diretos e/ou texto inline do container
                text = _inline_links(node)
                if text:
                    para_blocks.append({"type": "paragraph", "text": text})
            if para_blocks:
                last = sections[-1] if sections else None
                if last is not None:
                    last["blocks"].extend(para_blocks)
                else:
                    sections.append({"title": "", "blocks": para_blocks})
            return

        # ── legaltext-component (texto legal/rodapé de seção) ───────
        if "legaltext-component" in classes:
            para_blocks = []
            for p in node.find_all("p"):
                text = _inline_links(p)
                if text:
                    para_blocks.append({"type": "paragraph", "text": text})
            if para_blocks:
                last = sections[-1] if sections else None
                if last is not None:
                    last["blocks"].extend(para_blocks)
                else:
                    sections.append({"title": "", "blocks": para_blocks})
            return

        # ── tabs-component ──────────────────────────────────────────
        if "tabs-component" in classes and id(node) not in visited_tabs:
            visited_tabs.add(id(node))
            for tab_content in node.find_all("div", class_="tabs__content-item"):
                tab_name = tab_content.get("data-tab-name", "")
                if not tab_name:
                    continue
                blocks = []

                step_blocks = _extract_steps_from_container(tab_content)
                for sb in step_blocks:
                    blocks.append(sb)
                _mark_steps_visited(tab_content)

                for acc in tab_content.find_all("ul", class_="accordion"):
                    faq_items = extract_accordion_faqs(acc)
                    if faq_items:
                        blocks.append({"type": "faq", "items": faq_items})

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

        # ── h2 avulso ───────────────────────────────────────────────
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

        # ── <p class="h2"> ───────────────────────────────────────────
        if node.name == "p" and "h2" in classes and id(node) not in visited_h2:
            if not node.find_parent("div", class_="tabs__content-item"):
                visited_h2.add(id(node))
                text = clean_text(node.get_text())
                if text:
                    sections.append({"title": text + ".", "blocks": []})

        # ── steps-feature avulsos ───────────────────────────────────
        is_steps_container = (
            node.get("data-controller") == "steps-feature"
            or "steps-feature__container" in classes
        )
        if is_steps_container and id(node) not in visited_steps:
            if not node.find_parent("div", class_="tabs__content-item"):
                visited_steps.add(id(node))
                items = extract_steps_feature(node)
                if items:
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

        # ── <p> avulso fora de tabs/steps/teaser ────────────────────
        # Captura parágrafos em containers genéricos (richtext-component,
        # divs de grid AEM, comunicados não-duplicata já processados acima, etc.)
        # que não foram interceptados por nenhum handler específico acima.
        # Os parágrafos são anexados à última seção registrada.
        if node.name == "p":
            # Ignora: p.h2 (já tratado), p dentro de tabs/accordion/steps/teaser
            in_protected = (
                "h2" in classes
                or node.find_parent("div", class_="tabs__content-item")
                or node.find_parent("li",  class_="accordion__item")
                or node.find_parent("div", attrs={"data-controller": "steps-feature"})
                or node.find_parent("div", class_="steps-feature__container")
                or node.find_parent("div", class_="teaser")
                or node.find_parent("div", class_="end-of-page-component")
                or node.find_parent("div", class_="comunicados")
                or node.find_parent("div", class_="legaltext-component")
                or node.find_parent("div", class_="nav-links")
                or node.find_parent("div", class_="side-by-side-component")
            )
            if not in_protected:
                text = _inline_links(node)
                if text:
                    last = sections[-1] if sections else None
                    if last is not None:
                        last["blocks"].append({"type": "paragraph", "text": text})
                    else:
                        sections.append({"title": "", "blocks": [{"type": "paragraph", "text": text}]})
            return

        for child in node.children:
            if isinstance(child, Tag):
                walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag):
            walk(child)

    return [s for s in sections if s.get("title") or s.get("blocks")]


# ──────────────────────────────────────────────
# Extratores para CSV (mantidos para compatibilidade)
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