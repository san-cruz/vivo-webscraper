"""
Scraper Playwright para página Ativação Apple Music - Extrai informações completas
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import re
import os
from pathlib import Path
from playwright.sync_api import sync_playwright, Page, Locator


# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

URL = (
    "https://vivo.com.br/para-voce/produtos-e-servicos/servicos-digitais/"
    "ativacao-servicos-digitais/ativacao-apple-music"
)

# Pasta de saída relativa ao script
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_FILE = "apple-music.txt"


# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────

class BaseInfoScraperPlaywright(ABC):

    def __init__(self, url: str, headless: bool = True):
        self.url = url
        self.headless = headless

    def fetch_page(self, page: Page) -> None:
        try:
            page.goto(self.url, wait_until="domcontentloaded", timeout=60_000)
            page.wait_for_load_state("networkidle", timeout=60_000)
        except Exception as e:
            print(f"❌ Erro ao buscar página: {e}")
            raise

    @abstractmethod
    def extract_data(self, page: Page) -> Dict[str, Any]:
        pass

    @abstractmethod
    def format_output(self, data: Dict[str, Any]) -> str:
        pass

    def scrape(self) -> str:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/122.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            try:
                self.fetch_page(page)
                data = self.extract_data(page)
                return self.format_output(data)
            finally:
                context.close()
                browser.close()


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def clean_text(text: str) -> str:
    """Remove espaços extras e caracteres especiais comuns."""
    if not text:
        return ""
    text = text.replace("\xa0", " ").replace("&nbsp;", " ").replace("&nbsp", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_url(href: str) -> str:
    """Garante que URLs relativas se tornem absolutas."""
    if not href:
        return ""
    href = href.strip()
    if href.startswith("/"):
        return f"https://www.vivo.com.br{href}"
    if not href.startswith("http"):
        return f"https://{href}"
    return href


def text_or_empty(locator: Locator) -> str:
    """Retorna inner_text do primeiro match ou string vazia."""
    try:
        if locator.count() > 0:
            return clean_text(locator.first.inner_text())
    except Exception:
        pass
    return ""


def clean_step_title(raw: str) -> str:
    """
    Remove prefixo numérico e traço inicial de títulos de passo.
    Ex.: '1 - Baixe o app' → 'Baixe o app'
         '-Baixe o app'    → 'Baixe o app'
    """
    text = re.sub(r"^\d+\s*[-–]\s*", "", raw).strip()
    text = re.sub(r"^[-–]\s*", "", text).strip()
    return text


# ─────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────

class AtivacaoAppleMusicScraper(BaseInfoScraperPlaywright):

    # ------------------------------------------------------------------
    # Extração de rich-text: percorre filhos diretos para evitar duplicatas
    # ------------------------------------------------------------------
    def _extract_richtext_blocks(self, container: Locator) -> str:
        """
        Extrai texto de um bloco rich-text evitando duplicações causadas por
        selecionar tanto o <ul>/<ol> quanto seus <li> filhos.
        Estratégia: percorre apenas os filhos DIRETOS e ignora elementos
        que sejam containers de outros já processados.
        """
        parts: list[str] = []

        # Seleciona apenas filhos diretos relevantes, excluindo ul/ol
        # para não duplicar o texto dos <li>
        children = container.locator("> p, > li, > ul > li, > ol > li, > h3, > h4")
        seen: set[str] = set()

        for i in range(children.count()):
            child = children.nth(i)
            raw = clean_text(child.inner_text())
            if not raw or raw in seen:
                continue
            seen.add(raw)

            # Enriquece com links inline
            links = child.locator("a")
            enriched = raw
            for j in range(links.count()):
                link = links.nth(j)
                link_text = clean_text(link.inner_text())
                href = normalize_url(link.get_attribute("href") or "")
                if link_text and href and href not in enriched:
                    enriched = enriched.replace(link_text, f"{link_text} ({href})", 1)

            parts.append(enriched)

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Localiza heading (h1–h4 ou <p class="h2">) por texto parcial
    # ------------------------------------------------------------------
    def _find_heading(self, page: Page, tag: str, contains_text: str) -> Locator:
        # Tenta tag nativa primeiro; depois p com classe equivalente
        native = page.locator(tag).filter(has_text=contains_text).first
        if native.count() > 0:
            return native
        return page.locator(f"p.{tag}").filter(has_text=contains_text).first

    # ------------------------------------------------------------------
    # Extração principal
    # ------------------------------------------------------------------
    def extract_data(self, page: Page) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        print("📦 Extraindo informações Ativação Apple Music...\n")

        # 1. Título principal ────────────────────────────────────────────
        print("   🎯 Extraindo título principal...")
        main_title = page.locator("h1").filter(has_text="Saiba como ativar").first
        if main_title.count() > 0:
            data["titulo"] = clean_text(main_title.inner_text())
            print(f"      ✓ {data['titulo']}")

        # 2. Tabs de ativação ────────────────────────────────────────────
        print("   🎯 Extraindo tabs de ativação...")
        tabs_ativacao: list[dict] = []
        tabs_components = page.locator(".tabs-component")

        if tabs_components.count() > 0:
            tab_contents = tabs_components.nth(0).locator(".tabs__content-item")

            for i in range(tab_contents.count()):
                tab_content = tab_contents.nth(i)
                tab_name = clean_text(tab_content.get_attribute("data-tab-name") or "")
                passos: list[dict] = []
                steps = tab_content.locator(".steps-feature")

                for j in range(steps.count()):
                    step = steps.nth(j)

                    # Número do passo
                    numero_raw = text_or_empty(step.locator(".step-number span"))
                    numero = clean_text(numero_raw) if numero_raw else str(j + 1)

                    # Título — remove prefixo numérico/traço
                    titulo_raw = text_or_empty(step.locator(".step-text-title"))
                    titulo = clean_step_title(titulo_raw)

                    # Descrição — apenas o bloco dedicado, sem capturar botões
                    descricao = text_or_empty(step.locator(".step-text-description"))

                    # Botões de ação
                    botoes: list[dict] = []
                    botao_elems = step.locator(".step-buttons a")
                    btn_hrefs: set[str] = set()
                    for k in range(botao_elems.count()):
                        botao = botao_elems.nth(k)
                        btn_text = clean_text(botao.inner_text())
                        btn_href = normalize_url(botao.get_attribute("href") or "")
                        if btn_text and btn_href and btn_href not in btn_hrefs:
                            btn_hrefs.add(btn_href)
                            botoes.append({"texto": btn_text, "link": btn_href})

                    passos.append({
                        "numero": numero,
                        "titulo": titulo,
                        "descricao": descricao,
                        "botoes": botoes,
                    })

                tabs_ativacao.append({"nome": tab_name, "passos": passos})
                print(f"      ✓ {tab_name} ({len(passos)} passos)")

        data["tabs_ativacao"] = tabs_ativacao

        # 3. Mudanças de pagamento ───────────────────────────────────────
        print("   🎯 Extraindo mudanças de pagamento...")
        pagamento_title = self._find_heading(page, "h2", "Sobre mudanças dos meios de pagamento")
        if pagamento_title.count() > 0:
            comunicados = page.locator(".comunicados .richtext").first
            texto_pag = (
                self._extract_richtext_blocks(comunicados) if comunicados.count() > 0 else ""
            )
            data["mudancas_pagamento"] = {
                "titulo": clean_text(pagamento_title.inner_text()),
                "texto": texto_pag,
            }
            print("      ✓ Mudanças de pagamento")

        # 4. Vantagens da assinatura ─────────────────────────────────────
        print("   🎯 Extraindo vantagens da assinatura...")
        vantagens_section = page.locator(".photo-text-icon-component").first
        if vantagens_section.count() > 0:
            titulo_vant = text_or_empty(vantagens_section.locator(".teaser__title"))
            vantagens: list[str] = []
            icones = vantagens_section.locator(".teaser__icons__item")
            for i in range(icones.count()):
                texto = text_or_empty(icones.nth(i).locator(".teaser__icons__text"))
                if texto:
                    vantagens.append(texto)
            data["vantagens_assinatura"] = {"titulo": titulo_vant, "vantagens": vantagens}
            print(f"      ✓ {len(vantagens)} vantagens")

        # 5. FAQ ─────────────────────────────────────────────────────────
        print("   🎯 Extraindo FAQ...")
        faq_title = self._find_heading(page, "h2", "Tire suas dúvidas")
        tabs_faq: list[dict] = []

        faq_container = tabs_components.nth(1) if tabs_components.count() > 1 else None
        if faq_container:
            faq_tab_contents = faq_container.locator(".tabs__content-item")
            for i in range(faq_tab_contents.count()):
                tab_content = faq_tab_contents.nth(i)
                tab_name = clean_text(tab_content.get_attribute("data-tab-name") or "")
                perguntas: list[dict] = []
                accordion_items = tab_content.locator(".accordion__item")

                for j in range(accordion_items.count()):
                    item = accordion_items.nth(j)
                    pergunta = text_or_empty(item.locator(".accordion__item__label"))
                    richtext = item.locator(".richtext").first
                    resposta = (
                        self._extract_richtext_blocks(richtext) if richtext.count() > 0 else ""
                    )
                    if pergunta:
                        perguntas.append({"pergunta": pergunta, "resposta": resposta})

                tabs_faq.append({"nome": tab_name, "perguntas": perguntas})
                print(f"      ✓ {tab_name} ({len(perguntas)} perguntas)")

        data["faq"] = {
            "titulo": (
                clean_text(faq_title.inner_text()) if faq_title.count() > 0 else "Tire suas dúvidas"
            ),
            "tabs": tabs_faq,
        }

        # 6. Tutorial final ──────────────────────────────────────────────
        print("   🎯 Extraindo tutorial...")
        tutorial = page.locator(".end-of-page-component").first
        if tutorial.count() > 0:
            link_elem = tutorial.locator("a.end-page__item").first
            if link_elem.count() > 0:
                data["tutorial"] = {
                    "descricao": text_or_empty(link_elem.locator("p.body")),
                    "descricao_adicional": text_or_empty(link_elem.locator("p.body-2")),
                    "link": normalize_url(link_elem.get_attribute("href") or ""),
                }
                print("      ✓ Tutorial")

        total_passos = sum(len(t["passos"]) for t in tabs_ativacao)
        total_perguntas = sum(len(t["perguntas"]) for t in tabs_faq)
        print(f"\n   ✅ Extração concluída ({total_passos} passos, {total_perguntas} perguntas)\n")

        return data

    # ------------------------------------------------------------------
    # Formatação do .txt
    # ------------------------------------------------------------------
    def format_output(self, data: Dict[str, Any]) -> str:
        sections: list[str] = ["SEÇÃO: Ativação Apple Music\n"]

        # Título
        if data.get("titulo"):
            sections.append(data["titulo"])

        # Tabs de ativação
        for tab in data.get("tabs_ativacao", []):
            lines = [f"{tab['nome']}.", "Passos:"]
            for passo in tab["passos"]:
                # Linha principal do passo
                line = f"{passo['numero']}. {passo['titulo']}"
                if passo["descricao"]:
                    line += f" - {passo['descricao']}"
                lines.append(line)
                # Botões em linha separada, indentados
                for botao in passo["botoes"]:
                    lines.append(f"   Link: {botao['link']}")
            sections.append("\n".join(lines))

        # Mudanças de pagamento
        if data.get("mudancas_pagamento"):
            mp = data["mudancas_pagamento"]
            sections.append(f"{mp['titulo']}. {mp['texto']}")

        # Vantagens
        if data.get("vantagens_assinatura"):
            vant = data["vantagens_assinatura"]
            lines = [f"{vant['titulo']}."]
            for v in vant["vantagens"]:
                lines.append(f"- {v}")
            sections.append("\n".join(lines))

        # FAQ
        if data.get("faq"):
            faq = data["faq"]
            lines = [f"{faq['titulo']}."]
            for tab in faq["tabs"]:
                lines.append(f"\n{tab['nome']}:")
                for idx, p in enumerate(tab["perguntas"], 1):
                    lines.append(f"{idx}. {p['pergunta']}")
                    lines.append(p["resposta"])
            sections.append("\n".join(lines))

        # Tutorial
        if data.get("tutorial"):
            tut = data["tutorial"]
            desc = " ".join(filter(None, [tut["descricao"], tut["descricao_adicional"]]))
            sections.append(f"{desc}. Link: {tut['link']}")

        return "\n\n".join(sections)

    def scrape(self) -> str:
        print("🔍 Buscando página Ativação Apple Music...")
        return super().scrape()


# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = OUTPUT_DIR / OUTPUT_FILE

    scraper = AtivacaoAppleMusicScraper(URL, headless=True)
    resultado = scraper.scrape()

    output_path.write_text(resultado, encoding="utf-8")
    print(f"💾 Arquivo salvo em: {output_path}")