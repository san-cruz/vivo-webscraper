"""
Scraper Playwright para página Ativação Apple Music - Extrai informações completas
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import re
import os
from playwright.sync_api import sync_playwright, Page, Locator


# ─────────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────────

URL = (
    "https://vivo.com.br/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/ativacao-apple-music"
)

OUTPUT_FILE = "apple-music-2.txt"


# ─────────────────────────────────────────────
# BASE
# ─────────────────────────────────────────────

class BaseInfoScraperPlaywright(ABC):

    def __init__(self, url: str, headless: bool = True):
        self.url = url
        self.headless = headless

    def fetch_page(self, page: Page) -> None:
        try:
            page.goto(self.url, wait_until="domcontentloaded", timeout=60000)
            page.wait_for_load_state("networkidle", timeout=60000)
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
# SCRAPER
# ─────────────────────────────────────────────

class AtivacaoAppleMusicScraper(BaseInfoScraperPlaywright):

    def _clean_text(self, text: str) -> str:
        if not text:
            return ""
        text = text.replace("\xa0", " ").replace("&nbsp;", " ").replace("&nbsp", " ")
        text = re.sub(r"\s+", " ", text).strip()
        return text

    def _normalize_url(self, href: str) -> str:
        if not href:
            return ""
        if href.startswith("/"):
            return f"https://www.vivo.com.br{href}"
        if not href.startswith("http"):
            return f"https://{href}"
        return href

    def _text_or_empty(self, locator: Locator) -> str:
        try:
            if locator.count() > 0:
                return self._clean_text(locator.first.inner_text())
        except Exception:
            pass
        return ""

    def _find_heading(self, page: Page, tag: str, contains_text: str) -> Locator:
        # Aceita <h2> e também <p class="h2"> (comum em páginas Vivo)
        return page.locator(f"{tag}, p.{tag}").filter(has_text=contains_text).first

    def _extract_richtext_blocks(self, container: Locator) -> str:
        partes = []
        blocos = container.locator("p, li")
        for i in range(blocos.count()):
            bloco = blocos.nth(i)
            texto = self._clean_text(bloco.inner_text())
            links = bloco.locator("a")
            if links.count() > 0:
                for j in range(links.count()):
                    link = links.nth(j)
                    link_text = self._clean_text(link.inner_text())
                    href = self._normalize_url(link.get_attribute("href") or "")
                    if link_text and href and href not in texto:
                        texto = texto.replace(link_text, f"{link_text} ({href})")
            if texto:
                partes.append(texto)
        return self._clean_text(" ".join(partes))

    def extract_data(self, page: Page) -> Dict[str, Any]:
        data: Dict[str, Any] = {}

        print("📦 Extraindo informações Ativação Apple Music...\n")

        # 1. Título principal
        print("   🎯 Extraindo título principal...")
        main_title = self._find_heading(page, "h1", "Saiba como ativar")
        if main_title.count() > 0:
            data["titulo"] = self._clean_text(main_title.inner_text())
            print(f"      ✓ {data['titulo']}")

        # 2. Tabs de ativação
        print("   🎯 Extraindo tabs de ativação...")
        tabs_ativacao = []
        tabs_components = page.locator(".tabs-component")

        if tabs_components.count() > 0:
            tab_contents = tabs_components.nth(0).locator(".tabs__content-item")
            for i in range(tab_contents.count()):
                tab_content = tab_contents.nth(i)
                tab_name = self._clean_text(tab_content.get_attribute("data-tab-name") or "")
                passos = []
                steps = tab_content.locator(".steps-feature")
                for j in range(steps.count()):
                    step = steps.nth(j)
                    numero = self._text_or_empty(step.locator(".step-number span"))
                    titulo_raw = self._text_or_empty(step.locator(".step-text-title"))
                    descricao = self._text_or_empty(step.locator(".step-text-description"))
                    if not numero or numero.isspace():
                        numero = str(j + 1)
                    titulo = re.sub(r"^\d+\s*-\s*", "", titulo_raw).strip()
                    botoes = []
                    botao_elems = step.locator(".step-buttons a")
                    for k in range(botao_elems.count()):
                        botao = botao_elems.nth(k)
                        botao_text = self._clean_text(botao.inner_text())
                        botao_link = self._normalize_url(botao.get_attribute("href") or "")
                        if botao_text and botao_link:
                            botoes.append({"texto": botao_text, "link": botao_link})
                    passos.append({
                        "numero": numero,
                        "titulo": titulo,
                        "descricao": descricao,
                        "botoes": botoes
                    })
                tabs_ativacao.append({"nome": tab_name, "passos": passos})
                print(f"      ✓ {tab_name} ({len(passos)} passos)")

        data["tabs_ativacao"] = tabs_ativacao

        # 3. Mudanças de pagamento
        print("   🎯 Extraindo mudanças de pagamento...")
        pagamento_title = self._find_heading(page, "h2", "Sobre mudanças dos meios de pagamento")
        if pagamento_title.count() > 0:
            comunicados = page.locator(".comunicados .richtext").first
            texto_final = self._extract_richtext_blocks(comunicados) if comunicados.count() > 0 else ""
            data["mudancas_pagamento"] = {
                "titulo": self._clean_text(pagamento_title.inner_text()),
                "texto": texto_final
            }
            print("      ✓ Mudanças de pagamento")

        # 4. Vantagens da assinatura
        print("   🎯 Extraindo vantagens da assinatura...")
        vantagens_section = page.locator(".photo-text-icon-component").first
        if vantagens_section.count() > 0:
            titulo_vant = self._text_or_empty(vantagens_section.locator(".teaser__title"))
            vantagens = []
            icones = vantagens_section.locator(".teaser__icons__item")
            for i in range(icones.count()):
                texto = self._text_or_empty(icones.nth(i).locator(".teaser__icons__text"))
                if texto:
                    vantagens.append(texto)
            data["vantagens_assinatura"] = {"titulo": titulo_vant, "vantagens": vantagens}
            print(f"      ✓ {len(vantagens)} vantagens")

        # 5. FAQ (sempre pega o segundo .tabs-component, independente do título)
        print("   🎯 Extraindo FAQ...")
        faq_title = self._find_heading(page, "h2", "Tire suas dúvidas")
        tabs_faq = []

        faq_tabs_container = tabs_components.nth(1) if tabs_components.count() > 1 else None

        if faq_tabs_container:
            faq_tab_contents = faq_tabs_container.locator(".tabs__content-item")
            for i in range(faq_tab_contents.count()):
                tab_content = faq_tab_contents.nth(i)
                tab_name = self._clean_text(tab_content.get_attribute("data-tab-name") or "")
                perguntas = []
                accordion_items = tab_content.locator(".accordion__item")
                for j in range(accordion_items.count()):
                    item = accordion_items.nth(j)
                    pergunta = self._text_or_empty(item.locator(".accordion__item__label"))
                    richtext = item.locator(".richtext").first
                    resposta = self._extract_richtext_blocks(richtext) if richtext.count() > 0 else ""
                    perguntas.append({"pergunta": pergunta, "resposta": resposta})
                tabs_faq.append({"nome": tab_name, "perguntas": perguntas})
                print(f"      ✓ {tab_name} ({len(perguntas)} perguntas)")

        data["faq"] = {
            "titulo": self._clean_text(faq_title.inner_text()) if faq_title.count() > 0 else "Tire suas dúvidas",
            "tabs": tabs_faq
        }

        # 6. Tutorial final
        print("   🎯 Extraindo tutorial...")
        tutorial = page.locator(".end-of-page-component").first
        if tutorial.count() > 0:
            link_elem = tutorial.locator("a.end-page__item").first
            if link_elem.count() > 0:
                data["tutorial"] = {
                    "descricao": self._text_or_empty(link_elem.locator("p.body")),
                    "descricao_adicional": self._text_or_empty(link_elem.locator("p.body-2")),
                    "label": self._text_or_empty(link_elem.locator(".links-")),
                    "link": self._normalize_url(link_elem.get_attribute("href") or "")
                }
                print("      ✓ Tutorial")

        total_passos = sum(len(t["passos"]) for t in tabs_ativacao)
        total_perguntas = sum(len(t["perguntas"]) for t in tabs_faq)
        print(f"\n   ✅ Extração concluída ({total_passos} passos, {total_perguntas} perguntas)\n")

        return data

    def format_output(self, data: Dict[str, Any]) -> str:
        paragraphs = ["SEÇÃO: Ativação Apple Music\n"]

        if data.get("titulo"):
            paragraphs.append(data["titulo"])

        for tab in data.get("tabs_ativacao", []):
            tab_text = f"{tab['nome']}.\nPassos:"
            for passo in tab["passos"]:
                tab_text += f"\n{passo['numero']}. {passo['titulo']}"
                if passo["descricao"]:
                    tab_text += f" - {passo['descricao']}"
                for botao in passo["botoes"]:
                    tab_text += f" Link: {botao['link']}"
            paragraphs.append(tab_text)

        if data.get("mudancas_pagamento"):
            mp = data["mudancas_pagamento"]
            paragraphs.append(f"{mp['titulo']}. {mp['texto']}")

        if data.get("vantagens_assinatura"):
            vant = data["vantagens_assinatura"]
            vant_text = f"{vant['titulo']}."
            for v in vant["vantagens"]:
                vant_text += f"\n- {v}"
            paragraphs.append(vant_text)

        if data.get("faq"):
            faq = data["faq"]
            faq_text = f"{faq['titulo']}."
            for tab in faq["tabs"]:
                faq_text += f"\n\n{tab['nome']}:"
                for i, p in enumerate(tab["perguntas"], 1):
                    faq_text += f"\n{i}. {p['pergunta']}\n{p['resposta']}"
            paragraphs.append(faq_text)

        if data.get("tutorial"):
            tut = data["tutorial"]
            paragraphs.append(f"{tut['descricao']} {tut['descricao_adicional']}. Link: {tut['link']}")

        return "\n\n".join(paragraphs)

    def scrape(self) -> str:
        print("🔍 Buscando página Ativação Apple Music...")
        return super().scrape()


# ─────────────────────────────────────────────
# EXECUÇÃO
# ─────────────────────────────────────────────

if __name__ == "__main__":
    scraper = AtivacaoAppleMusicScraper(URL, headless=True)
    resultado = scraper.scrape()

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), OUTPUT_FILE)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(resultado)

    print(f"💾 Arquivo salvo em: {output_path}")
