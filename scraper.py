"""
Web Scraper com Playwright
--------------------------
Lê arquivos HTML da pasta /input, extrai dados e salva
em arquivos .txt e .csv na pasta /output.

Formato do .txt segue o padrão de documento de referência:
  SEÇÃO: <título da página>
  Subtítulos como cabeçalhos de bloco
  Listas numeradas com "Passos:" e itens "N. -texto"
  FAQs como "N. Pergunta\nResposta"
  Links inline: Link: <url>
"""

import asyncio
import csv
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright
from bs4 import BeautifulSoup, NavigableString, Tag

INPUT_DIR = Path(__file__).parent / "input"
OUTPUT_DIR = Path(__file__).parent / "output"


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove espaços extras e quebras de linha desnecessárias."""
    return re.sub(r"\s+", " ", text).strip()


def html_to_soup(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")


# ──────────────────────────────────────────────
# Extratores
# ──────────────────────────────────────────────

def extract_meta(soup: BeautifulSoup) -> dict:
    """Extrai título e descrição da página."""
    title = clean_text(soup.title.get_text()) if soup.title else ""
    description = ""
    for meta in soup.find_all("meta"):
        name = (meta.get("name") or meta.get("property") or "").lower()
        if name == "description":
            description = meta.get("content", "")
    return {"title": title, "description": description}


def extract_links(soup: BeautifulSoup) -> list[dict]:
    """Extrai todos os links (href + texto) para o CSV."""
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
    """Extrai tabelas HTML como lista de listas."""
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


def _inline_links(tag: Tag) -> str:
    """
    Reconstrói o texto de uma tag, inserindo ' Link: <href>' logo após
    cada âncora que tiver href, igual ao padrão do documento de referência.
    Evita duplicação: itera sobre filhos diretos e desce manualmente.
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


def extract_sections(soup: BeautifulSoup) -> list[dict]:
    """
    Percorre o DOM e agrupa o conteúdo em seções estruturadas.
    Cada seção tem:
      - title  : texto do heading (h1/h2/h3/h4)
      - blocks : lista de dicts com type e conteúdo
        type "paragraph"  → {"type": "paragraph", "text": "..."}
        type "ordered"    → {"type": "ordered",   "items": ["...", ...]}
        type "unordered"  → {"type": "unordered", "items": ["...", ...]}
        type "faq"        → {"type": "faq",       "items": [{"q":..,"a":..}, ...]}
    """
    # Tags que definem uma nova seção
    HEADING_TAGS = {"h1", "h2", "h3", "h4"}
    # Tags de conteúdo que vamos processar
    CONTENT_TAGS = {"p", "ul", "ol", "dl", "div"}

    sections: list[dict] = []
    current_section: dict | None = None

    def flush_section():
        if current_section and current_section["blocks"]:
            sections.append(current_section)

    def new_section(title: str):
        nonlocal current_section
        flush_section()
        current_section = {"title": title, "blocks": []}

    def add_block(block: dict):
        nonlocal current_section
        if current_section is None:
            current_section = {"title": "", "blocks": []}
        current_section["blocks"].append(block)

    # Detecta se uma <ul>/<ol> parece ser um FAQ:
    # cada <li> começa com um número seguido de ponto ou parêntese.
    def looks_like_faq(items: list[str]) -> bool:
        return sum(1 for it in items if re.match(r"^\d+[\.\)]", it)) >= len(items) // 2

    # Percorre apenas os filhos diretos de body ou do primeiro div principal
    body = soup.body or soup
    visited: set[int] = set()

    def process_node(node):
        if not isinstance(node, Tag):
            return
        if id(node) in visited:
            return
        visited.add(id(node))

        tag = node.name

        if tag in HEADING_TAGS:
            new_section(clean_text(node.get_text()))
            return

        if tag == "p":
            text = _inline_links(node)
            if text:
                add_block({"type": "paragraph", "text": text})
            return

        if tag in ("ul", "ol"):
            items = []
            for li in node.find_all("li", recursive=False):
                items.append(_inline_links(li))
            items = [it for it in items if it]
            if not items:
                return
            # Tenta detectar FAQ (perguntas numeradas dentro de listas)
            if looks_like_faq(items):
                faq_items = []
                for it in items:
                    # Remove prefixo numérico "1. " ou "1) "
                    it_clean = re.sub(r"^\d+[\.)\s]+", "", it).strip()
                    # Divide em pergunta (até o "?") e resposta (restante)
                    m = re.match(r"^(.+?\?)\s+(.+)$", it_clean, re.DOTALL)
                    if m:
                        q = clean_text(m.group(1))
                        a = clean_text(m.group(2))
                    else:
                        q = clean_text(it_clean)
                        a = ""
                    faq_items.append({"q": q, "a": a})
                add_block({"type": "faq", "items": faq_items})
            else:
                list_type = "ordered" if tag == "ol" else "unordered"
                add_block({"type": list_type, "items": items})
            return

        # Para divs e outros containers: desce recursivamente
        if tag in ("div", "section", "article", "main", "aside", "nav",
                   "header", "footer", "dl", "dt", "dd"):
            for child in node.children:
                process_node(child)

    for child in body.children:
        process_node(child)

    flush_section()

    # Remove seções e blocos vazios
    sections = [s for s in sections if s["blocks"]]
    return sections


# ──────────────────────────────────────────────
# Geração dos arquivos de saída
# ──────────────────────────────────────────────

def save_txt(stem: str, meta: dict, sections: list[dict]) -> Path:
    """
    Gera o .txt no padrão do documento de referência:

      SEÇÃO: <título da página>

      <Subtítulo>

      Passos:
      1. -item
      2. -item

      Sobre o serviço:
      1. Pergunta?
      Resposta.

      Texto livre em parágrafos.
    """
    path = OUTPUT_DIR / f"{stem}.txt"

    with open(path, "w", encoding="utf-8") as f:

        # Cabeçalho — SEÇÃO: <título>
        page_title = meta["title"] or stem
        f.write(f"SEÇÃO: {page_title}\n")
        if meta.get("description"):
            f.write(f"\n{meta['description']}\n")
        f.write("\n")

        for section in sections:
            # Título da seção (h1-h4)
            if section["title"]:
                f.write(f"\n{section['title']}\n\n")

            for block in section["blocks"]:

                if block["type"] == "paragraph":
                    f.write(f"{block['text']}\n")

                elif block["type"] == "ordered":
                    f.write("Passos:\n")
                    for i, item in enumerate(block["items"], 1):
                        f.write(f"{i}. -{item}\n")
                    f.write("\n")

                elif block["type"] == "unordered":
                    for item in block["items"]:
                        f.write(f"- {item}\n")
                    f.write("\n")

                elif block["type"] == "faq":
                    for i, faq in enumerate(block["items"], 1):
                        f.write(f"{i}. {faq['q']}\n")
                        if faq["a"]:
                            f.write(f"{faq['a']}\n")
                    f.write("\n")

            f.write("\n")

    return path


def save_csv_links(stem: str, links: list[dict]) -> Path:
    path = OUTPUT_DIR / f"{stem}_links.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "href"])
        writer.writeheader()
        writer.writerows(links)
    return path


def save_csv_texts(stem: str, text_blocks: list[str]) -> Path:
    path = OUTPUT_DIR / f"{stem}_textos.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["#", "texto"])
        for i, block in enumerate(text_blocks, 1):
            writer.writerow([i, block])
    return path


def save_csv_table(stem: str, table_index: int, rows: list[list[str]]) -> Path:
    path = OUTPUT_DIR / f"{stem}_tabela{table_index}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerows(rows)
    return path


# ──────────────────────────────────────────────
# Pipeline principal (usa Playwright para renderizar o HTML)
# ──────────────────────────────────────────────

async def process_html_file(page, html_path: Path) -> None:
    print(f"\n📄 Processando: {html_path.name}")

    # Carrega o arquivo HTML via Playwright (renderiza JS se houver)
    await page.goto(html_path.as_uri())
    await page.wait_for_load_state("networkidle")

    # Pega o HTML já renderizado (com JS executado)
    rendered_html = await page.content()
    soup = html_to_soup(rendered_html)

    meta = extract_meta(soup)
    sections = extract_sections(soup)
    links = extract_links(soup)
    tables = extract_tables(soup)

    stem = html_path.stem
    generated = []

    # ── Gera apenas o .txt no formato do documento de referência ──
    txt_path = save_txt(stem, meta, sections)
    generated.append(txt_path)

    # Descomente abaixo para gerar também os CSVs:
    # if links:
    #     generated.append(save_csv_links(stem, links))
    # generated.append(save_csv_texts(stem, [b["text"] for s in sections for b in s["blocks"] if b["type"] == "paragraph"]))
    # for i, table_rows in enumerate(tables, 1):
    #     generated.append(save_csv_table(stem, i, table_rows))

    print(f"   ✅ Título: {meta['title'] or '(sem título)'}")
    print(f"   📑 Seções extraídas: {len(sections)}")
    print(f"   🔗 Links: {len(links)}")
    print(f"   📊 Tabelas: {len(tables)}")
    print(f"   📁 Arquivos gerados:")
    for p in generated:
        print(f"      → {p.name}")


async def main():
    OUTPUT_DIR.mkdir(exist_ok=True)
    INPUT_DIR.mkdir(exist_ok=True)

    html_files = sorted(INPUT_DIR.glob("*.html")) + sorted(INPUT_DIR.glob("*.htm"))

    if not html_files:
        print("⚠️  Nenhum arquivo HTML encontrado em /input")
        print("   Coloque seus arquivos .html ou .htm na pasta 'input/' e rode novamente.")
        sys.exit(0)

    print(f"🚀 Iniciando scraper — {len(html_files)} arquivo(s) encontrado(s)\n")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        page = await browser.new_page()

        for html_file in html_files:
            try:
                await process_html_file(page, html_file)
            except Exception as e:
                print(f"   ❌ Erro ao processar {html_file.name}: {e}")

        await browser.close()

    print(f"\n🎉 Concluído! Arquivos salvos em: {OUTPUT_DIR.resolve()}")


if __name__ == "__main__":
    asyncio.run(main())
