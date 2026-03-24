# Vivo Scraper

Scraper das páginas informativas e estáticas do site Vivo, com saída em `.txt` estruturado por categoria.

> **Regra de inclusão:** apenas páginas sem seções de valores, pacotes ou planos comerciais são incluídas no catálogo.

---

## Requisitos

- Python 3.10+
- [Playwright](https://playwright.dev/python/) + Chromium
- BeautifulSoup4

```bash
pip install -r requirements.txt
playwright install chromium
```

---

## Estrutura do projeto

```
.
├── scrapertxt.py              # Script principal — gera os .txt completos
├── scrapertxt-faq.py          # Gera .txt somente com blocos de FAQ
├── scrapertxt-structured.py   # Gera .txt no formato estruturado (ex: canais)
├── scrapercsv.py              # Gera .csv (links, textos, tabelas) — só ativações
├── requirements.txt
│
├── extractors/                # Lógica de extração por categoria
│   ├── __init__.py            # Roteamento slug → extractor correto
│   ├── base.py                # Catálogo, helpers e componentes compartilhados
│   ├── ativacao-servicos-digitais.py
│   ├── ajuda-e-autoatendimento.py
│   ├── duvidas-internet-tv.py
│   ├── fatura.py
│   ├── vivo-explica.py
│   ├── por-que-vivo.py
│   └── conteudos-complementares.py
│
└── output/
    ├── outputs-txt/
    │   ├── ativacao-de-servicos-digitais/
    │   ├── duvidas-internet/
    │   ├── duvidas-tv/
    │   ├── ajuda-e-autoatendimento/
    │   ├── fatura/
    │   ├── vivo-explica/
    │   ├── por-que-vivo/
    │   └── conteudos-complementares/
    ├── outputs-txt-faqs/       # Saída do scrapertxt-faq.py
    └── outputs-txt-structured/ # Saída do scrapertxt-structured.py
```

---

## Uso — `scrapertxt.py`

Gera arquivos `.txt` completos com todo o conteúdo extraído de cada página.

```bash
# Todas as páginas do catálogo
python scrapertxt.py

# Slug específico
python scrapertxt.py ativacao-spotify

# Múltiplos slugs
python scrapertxt.py ativacao-spotify ativacao-netflix duvidas-internet-fibra

# Categoria inteira
python scrapertxt.py --category "Dúvidas — Internet"
python scrapertxt.py --category "Ativação de Serviços Digitais"

# Listar todos os slugs e URLs disponíveis
python scrapertxt.py --list

# Listar slugs de uma categoria específica
python scrapertxt.py --list --category "Vivo Explica"
```

---

## Uso — `scrapertxt-faq.py`

Extrai **apenas os blocos de FAQ** de cada página. Se a página não tiver FAQ, registra aviso no console e não gera arquivo.

Filtra automaticamente itens que não são perguntas reais (ex: blocos de "Termos e Condições", "Informações Gerais", "Regulamento"), mesmo que estejam dentro de um `faq-container-component`.

```bash
# Todas as páginas do catálogo
python scrapertxt-faq.py

# Slug específico
python scrapertxt-faq.py duvidas-internet-wifi

# Categoria inteira
python scrapertxt-faq.py --category "Fatura"

# Listar todos os slugs e URLs disponíveis
python scrapertxt-faq.py --list
```

### Formato dos arquivos gerados

Cada página com FAQ gera um arquivo em `output/outputs-txt-faqs/<categoria>/<slug>-faq.txt`.

```
SEÇÃO: Vivo dúvidas: Wi-Fi

1. Como trocar a senha do Wi-Fi?
1.1. Acesse o seu navegador e coloque na URL o endereço indicado na etiqueta
1.2. Entre com o seu login e senha conforme descrito na etiqueta
1.3. Clique na opção "Configurações", selecione a Rede Wi-Fi
Conferir mais dicas Link: https://vivo.com.br/para-voce/ajuda/resolva-agora/configuracoes-do-wi-fi

2. Qual frequência tenho no Wi-Fi da Vivo?
As redes Wi-Fi têm diferentes tipos de frequência, medidas em giga-hertz (GHz).
- A frequência 5GHz permite alta velocidade, mas tem área de cobertura menor
- A frequência 2.4 GHz permite uma área de cobertura maior, mas tem menos velocidade
```

### Itens filtrados (não são FAQ real)

Os títulos de acordeão a seguir são considerados blocos legais/informativos e são excluídos da saída:

- Informações Gerais / Informações Adicionais
- Preços e Tarifas / Preço e Tarifa
- Termos e Condições
- Regulamento
- Notas
- Vale Bonus / Vale Bônus
- Grade de Canais

---

## Uso — `scrapertxt-structured.py`

Gera arquivos `.txt` em **formato estruturado**, otimizado para páginas com múltiplas categorias de produtos, como `canais-adicionais`. O formato inclui cabeçalho, seção "Como Contratar", lista de categorias e campos detalhados por item (Nome, Descrição, Preço, Link).

```bash
# Todas as páginas do catálogo
python scrapertxt-structured.py

# Slug específico
python scrapertxt-structured.py canais-adicionais

# Categoria inteira
python scrapertxt-structured.py --category "Para Casa — TV"

# Listar todos os slugs e URLs disponíveis
python scrapertxt-structured.py --list
```

### Formato dos arquivos gerados

Cada página gera um arquivo em `output/outputs-txt-structured/<categoria>/<slug>-structured.txt`.

```
================================================================================
CANAIS ADICIONAIS – COMPLETE SEU PACOTE! | VIVO
================================================================================

Aproveite os canais adicionais Vivo TV e complemente sua programação.

COMO CONTRATAR:
- Via Aura, assistente virtual da Vivo
- Ligue 103 15 e fale com um especialista
- Pelo aplicativo Meu Vivo

================================================================================
CATEGORIAS DISPONÍVEIS:
  Filmes e Séries | Esportes | Adultos | Variedades | Internacionais
================================================================================

--------------------------------------------------------------------------------
FILMES E SÉRIES
--------------------------------------------------------------------------------

MAX
  Descrição    : Séries, filmes e muito mais com o melhor do entretenimento
  Preço        : R$ 34,90/mês
  Link         : https://vivo.com.br/para-voce/produtos-e-servicos/...

...

--------------------------------------------------------------------------------
ADULTOS
--------------------------------------------------------------------------------

  AVISO: A página pode conter imagens impróprias para menores de 18 anos.
  Acesso restrito a maiores de 18 anos.
  Link de acesso: https://vivo.com.br/...

...

================================================================================
Atenção
================================================================================
Oferta válida para clientes Vivo Fibra. Sujeito a disponibilidade na área.
================================================================================
```

---

## Formato dos arquivos `.txt` (scrapertxt.py)

Cada página gera um arquivo em `output/outputs-txt/<categoria>/<slug>.txt`.

### Páginas de ativação

```
SEÇÃO: Ativação Globoplay

Saiba como ativar sua assinatura Globoplay:

Não tenho conta.
Passos:
1. -Abra seu App Vivo - Baixe agora: Link: https://app.vivo/...
2. -Clique na aba "Assinaturas"
...

Confira tudo que sua assinatura Globoplay oferece.
- Pague seu plano Vivo e Globoplay na mesma fatura
- Acompanhe a programação dos canais Globo ao vivo
...
```

### Páginas de dúvidas / explica / por que vivo / conteúdos complementares

```
SEÇÃO: Vivo dúvidas: Wi-Fi

Vivo dúvidas: Wi-Fi
1. Como trocar a senha do Wi-Fi?
1.1. Acesse o seu navegador e coloque na URL o endereço indicado na etiqueta
1.2. Entre com o seu login e senha conforme descrito na etiqueta
1.3. Clique na opção "Configurações", selecione a Rede Wi-Fi
Conferir mais dicas Link: https://vivo.com.br/para-voce/ajuda/resolva-agora/configuracoes-do-wi-fi

2. Qual frequência tenho no Wi-Fi da Vivo?
As redes Wi-Fi têm diferentes tipos de frequência, medidas em giga-hertz (GHz).
- A frequência 5GHz permite alta velocidade, mas tem área de cobertura menor
- A frequência 2.4 GHz permite uma área de cobertura maior, mas tem menos velocidade
...
```

---

## Convenções de formatação (scrapertxt.py)

| Elemento | Formato no .txt |
|---|---|
| Título da página | `SEÇÃO: <título>` |
| Subtítulo (h2/h3) | linha em branco + texto |
| Subtítulo inline (p.body junto ao h2/h3) | parágrafo logo abaixo do título |
| Lista de passos (ol) | `Passos:\n1. -item` |
| Lista não-numerada (ul) | `- item` |
| FAQ — pergunta | `N. Pergunta?` |
| FAQ — subitem numerado (ol) | `N.1. texto` |
| FAQ — subitem não-numerado (ul) | `- texto` |
| FAQ — botão de ação | `Texto Link: https://...` (ao final da resposta) |
| Link inline | `texto Link: https://...` |
| Cards com link | `Descrição Link: https://...` |
| Cards tipo acesso rápido | `Título\nLink: https://...` |
| Links relativos | normalizados para `https://vivo.com.br/...` |

---

## Arquitetura dos extractors

Cada categoria tem seu próprio extractor em `extractors/`. O roteamento é feito automaticamente em `extractors/__init__.py` via `get_extractor(slug)`.

### Categorias e extractors

| Categoria | Extractor |
|---|---|
| Ativação de Serviços Digitais | `ativacao-servicos-digitais.py` |
| Ajuda e Autoatendimento | `ajuda-e-autoatendimento.py` |
| Dúvidas — Internet | `duvidas-internet-tv.py` |
| Dúvidas — TV | `duvidas-internet-tv.py` |
| Fatura | `fatura.py` |
| Vivo Explica | `vivo-explica.py` |
| Por que Vivo | `por-que-vivo.py` |
| Conteúdos Complementares | `conteudos-complementares.py` |

### Adicionar um novo extractor

1. Crie `extractors/<nome-da-categoria>.py` com uma função `extract_sections(soup, page_url="") -> list[dict]`
2. Importe de `extractors.base` os handlers que precisar
3. Registre a categoria em `_CATEGORY_TO_MODULE` no `extractors/__init__.py`

```python
# extractors/__init__.py
_CATEGORY_TO_MODULE: dict[str, str] = {
    ...
    "Nova Categoria": "extractors.nova-categoria",  # ← nova entrada
}
```

### Handlers disponíveis em `extractors/base.py`

#### Helpers de texto e navegação

| Função | Descrição |
|---|---|
| `clean_text(text)` | Remove espaços/quebras extras |
| `_inline_links(tag)` | Reconstrói texto com `Link: url` inline |
| `_normalize_href(href)` | Converte `/path` → `https://vivo.com.br/path` e `//` → `https://` |
| `append_to_last_section(sections, blocks)` | Anexa blocos à última seção registrada |
| `make_faq_duplicate_checker(soup)` | Retorna função que detecta parágrafos duplicados de FAQ |

#### Extratores de componentes

| Função | Descrição |
|---|---|
| `extract_steps_feature(container)` | Extrai passos do componente `.steps-feature` |
| `extract_accordion_faqs(container)` | Extrai FAQs simples (resposta como string inline) |
| `extract_accordion_faqs_formatted(container)` | FAQs com `N.1./N.2.` e `- item` |
| `collect_all_accordion_faqs(container)` | Agrupa todos os `ul.accordion` em lista única |
| `extract_side_by_side(container)` | Extrai items do componente `.side-by-side-component`; retorna `(items, is_card_layout)` |
| `_extract_card_blocks(card)` | Extrai título, preço, descrição e CTA de um card `.product-item` ou `.card-text` |
| `_extract_richtext_blocks(container)` | Extrai p/ul/ol/h3/h4 de um bloco richtext (modo simples) |
| `_extract_richtext_full(container)` | Extrai todo conteúdo textual de um container (modo completo, inclui h2/h3/h4) |

#### Handlers de seção (walk)

Cada handler recebe `(node, sections, visited, ...)`, retorna `True` se processou o nó (interrompendo o walk), `False` caso contrário.

| Handler | Componente tratado |
|---|---|
| `handle_highlight_product` | `highlight-product-component` (banner hero com richtext) |
| `handle_banner_secondary` | `banner-secondary-container-component` (slick ou slider direto) |
| `handle_banner_campanha` | `banner--campanha` (banner hero com `banner__text` + CTA) |
| `handle_slick_cards` | Slick slider com cards de produto |
| `handle_destaque_banner` | `destaque-banner` (cards com overline + h2/h3 + link) |
| `handle_tabs_component` | `tabs-component` (abas com steps, FAQ ou side-by-side) |
| `handle_steps_standalone` | `steps-feature` avulso fora de abas |
| `handle_faq_container` | `faq-container-component` |
| `handle_accordion_standalone` | `ul.accordion` avulso fora de faq-container |
| `handle_teaser` | `photo-text-component` / `.teaser` |
| `handle_comunicados` | `.comunicados` (bloco de texto rico) |
| `handle_richtext` | `.richtext` avulso fora de tabs/accordion/teaser |
| `handle_side_by_side_component` | `.side-by-side-component` |
| `handle_side_by_side_row` | `.side-by-side.row` (cards com `h4.card-text__title`) |
| `handle_h2` | `h2` em `div.title` (captura p.body subtítulo inline) |
| `handle_h3` | `h3` em `div.title` (captura p.body subtítulo inline) |
| `handle_p_h2` | `p.h2` (heading semântico) |
| `handle_p_h3` | `p.h3` (heading semântico) |
| `handle_cross` | `.cross` (cards de cross-sell com overline + p.h3 + span.h4) |
| `handle_destaque_banner` | `.destaque-banner` |
| `handle_see_all` | `.see-all-component` / `.vermais` |
| `handle_acesso_rapido` | `.acesso-rapido` (cards de navegação rápida) |
| `handle_nav_links` | `.nav-links` (índice de âncoras — links `#` descartados) |
| `handle_legaltext` | `.legaltext-component` |
| `handle_end_of_page` | `end-of-page-component` (captura itens com ou sem href válido) |
| `handle_button_component` | `.button-component` (botões CTA avulsos) |
| `handle_slider_products` | `online-store-container-component` (vitrine de produtos informativos) |
| `handle_p_standalone` | `p` avulso fora de containers protegidos |

#### Funções de catálogo e URL

| Função | Descrição |
|---|---|
| `fetch_main_content(page, url)` | Playwright: navega e retorna soup do `#main-content` |
| `extract_meta(soup)` | Extrai título e description da página |
| `build_url(slug)` | Retorna URL completa a partir do slug |
| `get_all_slugs()` | Lista todos os slugs do catálogo |
| `get_slugs_by_category(category)` | Filtra slugs por categoria |
| `get_categories()` | Lista categorias únicas na ordem do catálogo |
| `get_entry(slug)` | Retorna o dict completo de uma entrada do catálogo |

---

## Uso — `scrapercsv.py`

Processa apenas páginas da categoria **Ativação de Serviços Digitais**.

```bash
python scrapercsv.py                     # todas as páginas de ativação
python scrapercsv.py ativacao-netflix    # slug específico
python scrapercsv.py --list              # lista os slugs disponíveis
```

### Arquivos gerados por slug

| Arquivo | Conteúdo |
|---|---|
| `<slug>_links.csv` | Todos os links (texto + href) |
| `<slug>_textos.csv` | Blocos de texto extraídos |
| `<slug>_tabelaN.csv` | Tabelas HTML (se existirem) |