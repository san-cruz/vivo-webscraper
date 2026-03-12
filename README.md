# 🕷️ Web Scraper com Python + Playwright

Extrai dados de arquivos HTML e gera arquivos `.txt` e `.csv` organizados.

---

## 📁 Estrutura do Projeto

```
webscraper/
├── scraper.py          ← Script principal
├── requirements.txt    ← Dependências Python
├── input/              ← Coloque seus arquivos .html aqui
│   └── exemplo_produtos.html
└── output/             ← Arquivos gerados automaticamente aqui
```

---

## ⚙️ Instalação

### 1. Crie um ambiente virtual (recomendado)
```bash
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
.venv\Scripts\activate           # Windows
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Instale o browser do Playwright
```bash
playwright install chromium
```

---

## ▶️ Como Executar

1. Coloque seus arquivos `.html` ou `.htm` dentro da pasta `input/`
2. Rode o script:
```bash
python scrapertxt.py
```
3. Os resultados aparecerão na pasta `output/`

---

## 📤 Arquivos Gerados

Para cada `arquivo.html` na pasta `input/`, o scraper gera:

| Arquivo                      | Conteúdo                                      |
|------------------------------|-----------------------------------------------|
| `arquivo.txt`                | Metadados, todos os textos e links da página  |
| `arquivo_textos.csv`         | Todos os blocos de texto extraídos            |
| `arquivo_links.csv`          | Todos os links (texto + href)                 |
| `arquivo_tabela1.csv`        | Primeira tabela HTML encontrada               |
| `arquivo_tabela2.csv`        | Segunda tabela HTML (se existir), e assim...  |

---

## 🔍 Como Funciona

1. **Carregamento via Playwright**: O arquivo HTML é aberto em um browser Chromium headless. Isso significa que qualquer JavaScript da página é executado antes da extração — ideal para páginas dinâmicas.

2. **Parsing com BeautifulSoup**: O HTML renderizado é passado para o BeautifulSoup, que percorre as tags e extrai:
   - Metadados (`<title>`, `<meta name="description">`, etc.)
   - Blocos de texto (`<p>`, `<h1>`–`<h4>`, `<li>`, etc.)
   - Links (`<a href="...">`)
   - Tabelas (`<table>`)

3. **Geração dos arquivos**: Os dados extraídos são salvos em `.txt` (leitura humana) e `.csv` (uso em planilhas, pandas, etc.).

---

## 💡 Dicas

- Para adicionar mais extratores, edite as funções `extract_*` em `scraper.py`.
- Os CSVs gerados são compatíveis com Excel, Google Sheets e `pandas`.
- Para processar URLs ao vivo (não só arquivos locais), troque `page.goto(html_path.as_uri())` por `page.goto("https://...")`.
