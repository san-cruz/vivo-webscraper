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
# Extratores especializados para componentes Vivo
# ──────────────────────────────────────────────

def extract_steps_feature(container: Tag) -> list[dict]:
    """
    Extrai passos do componente .steps-feature da Vivo.
    Cada passo tem um título (.step-text-title) e opcionalmente
    uma descrição (.step-text-description) e botões com links.
    Retorna lista de strings no formato "Título - Descrição Link: url"
    """
    items = []
    for step_div in container.find_all("div", class_="step"):
        # Título do passo
        title_tag = step_div.find(class_="step-text-title")
        if not title_tag:
            continue

        # Remove o span oculto de número dentro do título
        for hidden in title_tag.find_all("span", class_="hide-text"):
            hidden.decompose()

        title_text = clean_text(title_tag.get_text())

        # Descrição
        desc_tag = step_div.find(class_="step-text-description")
        desc_text = clean_text(desc_tag.get_text()) if desc_tag else ""

        # Links dos botões do passo (ex: Play Store, App Store, App Vivo)
        # Pega apenas links hide-mobile para evitar duplicação
        step_links = []
        btn_div = step_div.find(class_="step-buttons")
        if btn_div:
            for a in btn_div.find_all("a", href=True):
                # Ignora versão mobile duplicada
                classes = a.get("class", [])
                if "hide-desktop" in classes:
                    continue
                href = a["href"].strip()
                if href and not href.startswith("#"):
                    step_links.append(href)

        # Monta o texto do passo
        # Título e descrição são separados por " - "
        # Links são acrescentados com " Link: " (sem traço)
        base_parts = [title_text]
        if desc_text:
            base_parts.append(desc_text)
        base = " - ".join(base_parts)

        seen_links = set()
        for href in step_links:
            if href not in seen_links:
                base += f" Link: {href}"
                seen_links.add(href)

        items.append(base)

    return items


def extract_accordion_faqs(container: Tag) -> list[dict]:
    """
    Extrai FAQs de componentes .accordion da Vivo.
    Cada item tem um label (pergunta) e um container (resposta).
    """
    faq_items = []
    for li in container.find_all("li", class_="accordion__item"):
        # Pergunta: botão label
        btn = li.find("button", class_="accordion__item__label")
        if not btn:
            continue
        # Remove o span de arrow
        for span in btn.find_all("span", class_="accordion__item__attach"):
            span.decompose()
        question = clean_text(btn.get_text())

        # Resposta: conteúdo do container
        content_div = li.find(class_="accordion__item__container")
        answer = _inline_links(content_div) if content_div else ""

        faq_items.append({"q": question, "a": answer})

    return faq_items


def extract_tabs(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai componentes de abas (.tabs-component) da Vivo.
    Retorna lista de seções com título e blocos de conteúdo,
    processando cada aba como uma sub-seção.
    """
    sections = []

    for tabs_component in soup.find_all("div", class_="tabs-component"):
        tab_contents = tabs_component.find_all("div", class_="tabs__content-item")

        for tab_content in tab_contents:
            tab_name_attr = tab_content.get("data-tab-name", "")
            if not tab_name_attr:
                continue

            blocks = []

            # Verifica se tem steps-feature (passos do tutorial)
            steps_containers = tab_content.find_all(
                "div", attrs={"data-controller": "steps-feature"}
            )
            for steps_container in steps_containers:
                items = extract_steps_feature(steps_container)
                if items:
                    blocks.append({"type": "ordered", "items": items})

            # Verifica se tem accordion (FAQs)
            accordion_containers = tab_content.find_all(
                "ul", class_="accordion"
            )
            for accordion in accordion_containers:
                faq_items = extract_accordion_faqs(accordion)
                if faq_items:
                    blocks.append({"type": "faq", "items": faq_items})

            if blocks:
                sections.append({
                    "title": tab_name_attr + ".",
                    "blocks": blocks
                })

    return sections


def extract_teaser_icons(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai itens de ícone do componente .teaser__icons da Vivo.
    Retorna seções com título (teaser__title) e lista de itens.
    """
    sections = []
    for teaser in soup.find_all("div", class_="teaser"):
        title_tag = teaser.find(class_="teaser__title")
        if not title_tag:
            continue
        title = clean_text(title_tag.get_text())

        items = []
        for icon_item in teaser.find_all(class_="teaser__icons__text"):
            text = clean_text(icon_item.get_text())
            if text:
                items.append(text)

        if items:
            sections.append({
                "title": title + ".",
                "blocks": [{"type": "unordered", "items": items}]
            })

    return sections


def extract_richtext_blocks(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai blocos de richtext (.comunicados) que não estão dentro de abas.
    """
    sections = []
    for rt_div in soup.find_all("div", class_="comunicados"):
        # Verifica se está dentro de uma aba (já tratada)
        if rt_div.find_parent("div", class_="tabs__content-item"):
            continue
        paras = []
        for p in rt_div.find_all("p"):
            text = _inline_links(p)
            if text:
                paras.append({"type": "paragraph", "text": text})
        if paras:
            sections.append({"title": "", "blocks": paras})
    return sections


def extract_end_page(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai o componente de fim de página (.end-of-page-component).
    """
    sections = []
    for end in soup.find_all("div", class_="end-of-page-component"):
        for a in end.find_all("a", href=True):
            href = a["href"].strip()
            if href.startswith("#"):
                continue
            # Pega todo o texto do link
            text_parts = []
            for p in a.find_all("p"):
                t = clean_text(p.get_text())
                if t:
                    text_parts.append(t)
            if text_parts:
                full_text = " ".join(text_parts) + f" Link: {href}"
                sections.append({
                    "title": "",
                    "blocks": [{"type": "paragraph", "text": full_text}]
                })
    return sections


def extract_page_title_section(soup: BeautifulSoup) -> list[dict]:
    """
    Extrai o título principal (h1) e a descrição imediata da página.
    """
    sections = []
    h1 = soup.find("h1")
    if not h1:
        return sections

    title_text = clean_text(h1.get_text())
    blocks = []

    # Busca parágrafos próximos ao h1 (irmãos ou dentro do mesmo container)
    container = h1.find_parent("div", class_="container")
    if container:
        # Procura richtext próximo ao title component
        title_comp = h1.find_parent(class_="title")
        if title_comp:
            next_sib = title_comp.find_next_sibling()
            # Pula spacers
            while next_sib and "spacer" in next_sib.get("class", []):
                next_sib = next_sib.find_next_sibling()
            # Se não for tabs, pega parágrafos
            if next_sib and "tabs-component" not in next_sib.get("class", []):
                for p in next_sib.find_all("p"):
                    text = _inline_links(p)
                    if text:
                        blocks.append({"type": "paragraph", "text": text})

    sections.append({"title": title_text, "blocks": blocks})
    return sections


# ──────────────────────────────────────────────
# Pipeline de extração principal
# ──────────────────────────────────────────────

def extract_sections(soup: BeautifulSoup) -> list[dict]:
    """
    Orquestra a extração de todas as seções da página seguindo a ordem do DOM.
    Percorre os nós de alto nível e delega para extratores especializados.
    """
    sections = []

    # 1. Título principal (h1)
    sections.extend(extract_page_title_section(soup))

    # 2. Percorre o DOM em ordem para capturar tabs, teasers, h2 e end-page
    #    na mesma sequência em que aparecem na página.
    visited_tabs: set[int] = set()
    visited_teasers: set[int] = set()
    visited_h2: set[int] = set()
    visited_end: set[int] = set()

    def walk(node: Tag):
        if not isinstance(node, Tag):
            return

        classes = node.get("class", [])

        # tabs-component → processa todas as abas internas em ordem
        if "tabs-component" in classes and id(node) not in visited_tabs:
            visited_tabs.add(id(node))
            for tab_content in node.find_all("div", class_="tabs__content-item"):
                tab_name = tab_content.get("data-tab-name", "")
                if not tab_name:
                    continue
                blocks = []
                # Passos (steps-feature)
                for sc in tab_content.find_all(
                    "div", attrs={"data-controller": "steps-feature"}
                ):
                    items = extract_steps_feature(sc)
                    if items:
                        blocks.append({"type": "ordered", "items": items})
                # Accordions (FAQ)
                for acc in tab_content.find_all("ul", class_="accordion"):
                    faq_items = extract_accordion_faqs(acc)
                    if faq_items:
                        blocks.append({"type": "faq", "items": faq_items})
                if blocks:
                    sections.append({"title": tab_name + ".", "blocks": blocks})
            return  # não desce mais

        # teaser com ícones
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
                    sections.append({"title": title, "blocks": [
                        {"type": "unordered", "items": items}
                    ]})
                return

        # h2 avulso (fora de abas e teasers)
        if node.name in ("h2",) and id(node) not in visited_h2:
            if not node.find_parent("div", class_="tabs__content-item") and \
               not node.find_parent("div", class_="teaser"):
                visited_h2.add(id(node))
                h2_text = clean_text(node.get_text())
                blocks = []
                # richtext/.comunicados imediatamente após
                title_comp = node.find_parent(class_="title")
                if title_comp:
                    sib = title_comp.find_next_sibling()
                    while sib and "spacer" in sib.get("class", []):
                        sib = sib.find_next_sibling()
                    if sib:
                        for p in sib.find_all("p"):
                            text = _inline_links(p)
                            if text:
                                blocks.append({"type": "paragraph", "text": text})
                sections.append({"title": h2_text, "blocks": blocks})

        # <p class="h2"> (ex: "Tire suas dúvidas sobre Apple Music")
        if node.name == "p" and "h2" in classes and id(node) not in visited_h2:
            if not node.find_parent("div", class_="tabs__content-item"):
                visited_h2.add(id(node))
                text = clean_text(node.get_text())
                if text:
                    sections.append({"title": text + ".", "blocks": []})

        # end-of-page
        if "end-of-page-component" in classes and id(node) not in visited_end:
            visited_end.add(id(node))
            for a in node.find_all("a", href=True):
                href = a["href"].strip()
                if href.startswith("#"):
                    continue
                text_parts = [clean_text(p.get_text()) for p in a.find_all("p")
                              if clean_text(p.get_text())]
                if text_parts:
                    full = " ".join(text_parts) + f" Link: {href}"
                    sections.append({"title": "", "blocks": [
                        {"type": "paragraph", "text": full}
                    ]})
            return

        # Desce nos filhos
        for child in node.children:
            if isinstance(child, Tag):
                walk(child)

    body = soup.body or soup
    for child in body.children:
        if isinstance(child, Tag):
            walk(child)

    # Remove seções completamente vazias
    sections = [s for s in sections if s.get("title") or s.get("blocks")]
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
                f.write(f"\n{section['title']}\n")

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