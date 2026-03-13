# Vivo Digital Services Scraper

Scraper das páginas de ativação de serviços digitais da Vivo (`/para-voce/produtos-e-servicos/servicos-digitais/ativacao-servicos-digitais/*`), com saída em `.txt` e `.csv`.

---

## Requisitos

- Python 3.10+
- [Playwright](https://playwright.dev/python/) + Chromium
- BeautifulSoup4

```bash
pip install -r requirements.txt

playwright install chromium 
ou
python -m playwright install chromium
```

---

## Estrutura

```
.
├── extractor.py      # Lógica central de extração (compartilhada)
├── scrapertxt.py     # Gera arquivos .txt estruturados
├── scapercsv.py      # Gera arquivos .csv (links, textos, tabelas)
├── requirements.txt
└── output/
    ├── txt/          # Saída dos .txt
    └── csv/          # Saída dos .csv
```

---

## Uso

### Gerar `.txt`
```bash
python scrapertxt.py                      # todas as páginas
python scrapertxt.py ativacao-spotify     # página específica
python scrapertxt.py --list               # lista os slugs disponíveis
```

### Gerar `.csv`
```bash
python scapercsv.py                       # todas as páginas
python scapercsv.py ativacao-netflix      # página específica
python scapercsv.py --list                # lista os slugs disponíveis
```

---

## Saídas

**`.txt`** — um arquivo por página com conteúdo estruturado (título, passos, FAQs, listas).

**`.csv`** — três tipos de arquivo por página:

| Arquivo | Conteúdo |
|---|---|
| `<slug>_links.csv` | Todos os links (texto + href) |
| `<slug>_textos.csv` | Blocos de texto extraídos |
| `<slug>_tabelaN.csv` | Tabelas HTML (se existirem) |

---

## Páginas suportadas

| Slug | Serviço |
|---|---|
| `ativacao-apple-music` | Apple Music |
| `ativacao-spotify` | Spotify |
| `ativacao-netflix` | Netflix |
| `ativacao-globoplay` | Globoplay |
| `ativacao-max` | Max |
| `ativacao-amazon-prime` | Amazon Prime |
| `ativacao-telecine` | Telecine |
| `ativacao-premiere` | Premiere |
| `ativacao-youtube-premium` | YouTube Premium |
| `ativacao-vivo-tv` | Vivo TV |
| `ativacao-vivae` | Vivaê |
| `ativacao-vale-saude` | Vale Saúde |
| `ativacao-ip-fixo-digital` | IP Fixo Digital |