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
├── scrapertxt.py              # Script principal — gera os .txt
├── scrapercsv.py              # Gera .csv (links, textos, tabelas) — só ativações
├── requirements.txt
│
├── extractors/                # Lógica de extração por categoria
│   ├── __init__.py            # Roteamento slug → extractor correto
│   ├── base.py                # Catálogo, helpers e componentes compartilhados
│   ├── ativacao-servicos-digitais.py   # Extractor para páginas de ativação
│   └── duvidas-internet-tv.py          # Extractor para páginas de dúvidas
│
└── output/
    └── txt/
        ├── ativacao-de-servicos-digitais/
        ├── duvidas-internet/
        ├── duvidas-tv/
        ├── ajuda-e-autoatendimento/     # ⏭️ sem extractor ainda
        ├── fatura/                      # ⏭️ sem extractor ainda
        ├── vivo-explica/                # ⏭️ sem extractor ainda
        ├── por-que-vivo/                # ⏭️ sem extractor ainda
        └── conteudos-complementares/    # ⏭️ sem extractor ainda
```

---

## Uso — `scrapertxt.py`

```bash
# Todas as páginas do catálogo (47 páginas, 8 categorias)
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
python scrapertxt.py --list --category "Dúvidas — TV"
```

> Páginas de categorias **sem extractor** são puladas automaticamente com aviso `⏭️ Pulado`, sem interromper o processo.

---

## Formato dos arquivos `.txt`

Cada página gera um arquivo em `output/txt/<categoria>/<slug>.txt`.

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

Tire suas dúvidas sobre Globoplay.

Sobre o Serviço.
1. Contratei o plano Vivo Fibra com Globoplay, quando posso começar a usá-lo?
O Globoplay estará disponível para ativação após a instalação da Fibra.
...
```

### Páginas de dúvidas (internet / TV)

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
Sempre que possível, dê preferência ao 5GHz.
...

Wi-Fi na casa toda com o Repetidor Vivo Smart Wi-Fi!.
Ele melhora o sinal da internet em locais onde o Wi-Fi tem dificuldade de chegar, como:
- Casas e apartamentos com mais de um andar
- Imóveis com formato em L
Comprar Repetidor Link: https://store.vivo.com.br/...

Informações práticas para o seu dia a dia
Veja dicas para aproveitar ao máximo seu wi-fi Link: https://vivo.com.br/...
Aprenda a escolher o melhor roteador para suas necessidades Link: https://vivo.com.br/...

Dúvidas sobre outro assunto?
Celular
Link: https://vivo.com.br/para-voce/ajuda/duvidas/celular
Internet
Link: https://vivo.com.br/para-voce/ajuda/duvidas/internet
```

---

## Convenções de formatação

| Elemento | Formato no .txt |
|---|---|
| Título da página | `SEÇÃO: <título>` |
| Subtítulo (h2) | linha em branco + texto |
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

Cada categoria tem seu próprio extractor especializado na pasta `extractors/`. O roteamento é feito automaticamente em `extractors/__init__.py` via `get_extractor(slug)`.

### Adicionar um novo extractor

1. Crie `extractors/<nome-da-categoria>.py` com uma função `extract_sections(soup) -> list[dict]`
2. Importe de `extractors.base` os helpers que precisar
3. Registre a categoria em `_CATEGORY_TO_MODULE` no `extractors/__init__.py`
4. Remova a categoria de `_FALLBACK_CATEGORIES` no mesmo arquivo

```python
# extractors/__init__.py
_CATEGORY_TO_MODULE: dict[str, str] = {
    "Ativação de Serviços Digitais": "extractors.ativacao-servicos-digitais",
    "Dúvidas — Internet":            "extractors.duvidas-internet-tv",
    "Dúvidas — TV":                  "extractors.duvidas-internet-tv",
    "Fatura":                        "extractors.fatura",  # ← nova entrada
}
```

### Helpers disponíveis em `extractors/base.py`

| Função | Descrição |
|---|---|
| `clean_text(text)` | Remove espaços/quebras extras |
| `_inline_links(tag)` | Reconstrói texto com `Link: url` inline |
| `_normalize_href(href)` | Converte `/path` → `https://vivo.com.br/path` |
| `extract_steps_feature(container)` | Extrai passos do componente `.steps-feature` |
| `extract_accordion_faqs(container)` | Extrai FAQs simples (resposta como string inline) |
| `extract_accordion_faqs_formatted(container)` | FAQs com `N.1./N.2.` e `- item` |
| `collect_all_accordion_faqs(container)` | Agrupa todos os `ul.accordion` em uma lista única |
| `extract_side_by_side(container)` | Extrai items do componente `.side-by-side-component` |
| `_extract_richtext_blocks(container)` | Extrai p/ul/ol/h3/h4 de um bloco richtext |
| `fetch_main_content(page, url)` | Playwright: navega e retorna soup do `#main-content` |
| `extract_meta(soup)` | Extrai título e description da página |
| `build_url(slug)` | Retorna URL completa a partir do slug |
| `get_all_slugs()` | Lista todos os slugs do catálogo |
| `get_slugs_by_category(category)` | Filtra slugs por categoria |

---

## Catálogo de páginas (47 páginas)

### ✅ Ativação de Serviços Digitais (14) — extractor pronto

| Slug | Serviço |
|---|---|
| `ativacao-amazon-prime` | Amazon Prime |
| `ativacao-apple-music` | Apple Music |
| `ativacao-disney-plus` | Disney+ |
| `ativacao-globoplay` | Globoplay |
| `ativacao-max` | Max |
| `ativacao-netflix` | Netflix |
| `ativacao-premiere` | Premiere |
| `ativacao-spotify` | Spotify |
| `ativacao-telecine` | Telecine |
| `ativacao-vivo-play` | Vivo Play |
| `ativacao-vivae` | Vivaê |
| `ativacao-vale-saude` | Vale Saúde |
| `ativacao-mcafee` | McAfee |
| `ativacao-ip-fixo-digital` | IP Fixo Digital |

### ✅ Dúvidas — Internet (3) — extractor pronto

| Slug | Página |
|---|---|
| `duvidas-internet-wifi` | Internet Vivo Wi-Fi |
| `duvidas-internet-fibra` | Internet Fibra |
| `duvidas-internet-vivo-total` | Internet Vivo Total |

### ✅ Dúvidas — TV (4) — extractor pronto

| Slug | Página |
|---|---|
| `duvidas-tv-fibra` | TV Fibra |
| `duvidas-tv-apps-canais` | TV Apps de Canais |
| `duvidas-tv-assinatura` | TV Assinatura |
| `duvidas-tv-online` | TV Online |

### ⏭️ Ajuda e Autoatendimento (9) — sem extractor

| Slug | Página |
|---|---|
| `app-vivo` | App Vivo |
| `mais-ajuda` | Mais Ajuda |
| `encontre-uma-loja` | Encontre uma Loja |
| `dicas-wifi` | Dicas Wi-Fi |
| `mudanca-de-endereco` | Mudança de Endereço |
| `servico-de-instalacao` | Serviço de Instalação |
| `portabilidade` | Portabilidade |
| `ativando-o-chip` | Ativando o Chip |
| `consumo-de-internet` | Consumo de Internet |

### ⏭️ Fatura (7) — sem extractor

| Slug | Página |
|---|---|
| `2-via-de-fatura` | 2ª Via de Fatura |
| `entenda-sua-fatura` | Entenda sua Fatura |
| `fatura-digital` | Fatura Digital |
| `debito-automatico` | Débito Automático |
| `negociacao-de-debitos` | Negociação de Débitos |
| `pagamento` | Pagamento |
| `bloqueio-de-linha` | Bloqueio de Linha |

### ⏭️ Vivo Explica (3) — sem extractor

| Slug | Página |
|---|---|
| `explica-internet-wifi` | Internet e Wi-Fi |
| `explica-smartphones-eletronicos` | Smartphones e Eletrônicos |
| `explica-dicionario-velocidade` | Dicionário de Velocidade da Internet |

### ⏭️ Por que Vivo (4) — sem extractor

| Slug | Página |
|---|---|
| `teste-de-velocidade` | Teste de Velocidade |
| `premios` | Prêmios |
| `vivo-renova` | Vivo Renova |
| `vivo-valoriza` | Vivo Valoriza |

### ⏭️ Conteúdos Complementares (3) — sem extractor

| Slug | Página |
|---|---|
| `beneficios-vivo-tv` | Benefícios Vivo TV |
| `apps-inclusos-plano-internet` | Apps Inclusos no Plano de Internet |
| `vivo-smart-wifi` | Vivo Smart Wi-Fi |

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