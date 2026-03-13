# Vivo Digital Services Scraper

Scraper das páginas informativas e estáticas do site Vivo, com saída em `.txt` organizada por categoria.

> **Regra de inclusão:** apenas páginas sem seções de valores, pacotes ou planos comerciais são incluídas no catálogo.

---

## Requisitos

- Python 3.10+
- [Playwright](https://playwright.dev/python/) + Chromium
- BeautifulSoup4

```bash
pip install -r requirements.txt

playwright install chromium
# ou
python -m playwright install chromium
```

---

## Estrutura

```
.
├── extractor.py      # Lógica central de extração (compartilhada)
├── scrapertxt.py     # Gera arquivos .txt estruturados
├── scrapercsv.py     # Gera arquivos .csv (links, textos, tabelas)
├── requirements.txt
└── output/
    └── txt/
        ├── ativacao-de-servicos-digitais/
        ├── ajuda-e-autoatendimento/
        ├── fatura/
        ├── duvidas-internet/
        ├── duvidas-tv/
        ├── vivo-explica/
        ├── por-que-vivo/
        └── conteudos-complementares/
```

---

## Uso — `scrapertxt.py`

```bash
# Todas as páginas do catálogo (47 páginas, 8 categorias)
python scrapertxt.py

# Slug específico
python scrapertxt.py ativacao-spotify

# Múltiplos slugs
python scrapertxt.py ativacao-spotify ativacao-netflix dicas-wifi

# Categoria inteira
python scrapertxt.py --category "Fatura"
python scrapertxt.py --category "Dúvidas — TV"

# Listar todos os slugs e URLs disponíveis
python scrapertxt.py --list

# Listar slugs de uma categoria específica
python scrapertxt.py --list --category "Ajuda e Autoatendimento"
```

### Saída

Um arquivo `.txt` por página, salvo na subpasta correspondente à sua categoria:

```
output/txt/ativacao-de-servicos-digitais/ativacao-spotify.txt
output/txt/fatura/entenda-sua-fatura.txt
output/txt/duvidas-tv/duvidas-tv-fibra.txt
```

### Formato do `.txt`

```
SEÇÃO: <título da página>

<Subtítulo H2>

Passos:
1. -Passo um
2. -Passo dois

Subtítulo de FAQ:
1. Pergunta?
Resposta.

- item de lista
```

---

## Uso — `scrapercsv.py`

Processa apenas as páginas da categoria **Ativação de Serviços Digitais**.

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

---

## Catálogo de páginas (47 páginas)

### Ativação de Serviços Digitais (14)

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

### Ajuda e Autoatendimento (9)

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

### Fatura (7)

| Slug | Página |
|---|---|
| `2-via-de-fatura` | 2ª Via de Fatura |
| `entenda-sua-fatura` | Entenda sua Fatura |
| `fatura-digital` | Fatura Digital |
| `debito-automatico` | Débito Automático |
| `negociacao-de-debitos` | Negociação de Débitos |
| `pagamento` | Pagamento |
| `bloqueio-de-linha` | Bloqueio de Linha |

### Dúvidas — Internet (3)

| Slug | Página |
|---|---|
| `duvidas-internet-wifi` | Internet Vivo Wi-Fi |
| `duvidas-internet-fibra` | Internet Fibra |
| `duvidas-internet-vivo-total` | Internet Vivo Total |

### Dúvidas — TV (4)

| Slug | Página |
|---|---|
| `duvidas-tv-fibra` | TV Fibra |
| `duvidas-tv-apps-canais` | TV Apps de Canais |
| `duvidas-tv-assinatura` | TV Assinatura |
| `duvidas-tv-online` | TV Online |

### Vivo Explica (3)

| Slug | Página |
|---|---|
| `explica-internet-wifi` | Internet e Wi-Fi |
| `explica-smartphones-eletronicos` | Smartphones e Eletrônicos |
| `explica-dicionario-velocidade` | Dicionário de Velocidade da Internet |

### Por que Vivo (4)

| Slug | Página |
|---|---|
| `teste-de-velocidade` | Teste de Velocidade |
| `premios` | Prêmios |
| `vivo-renova` | Vivo Renova |
| `vivo-valoriza` | Vivo Valoriza |

### Conteúdos Complementares (3)

| Slug | Página |
|---|---|
| `beneficios-vivo-tv` | Benefícios Vivo TV |
| `apps-inclusos-plano-internet` | Apps Inclusos no Plano de Internet |
| `vivo-smart-wifi` | Vivo Smart Wi-Fi |