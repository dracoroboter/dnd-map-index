# Linea C — dnd-map-index: Indice mappe D&D libere

**Stato**: pianificazione completata, tutte le decisioni prese
**Priorità**: attiva
**Repo**: separato `dnd-map-index` — licenza GPL2
**Aggiornato**: 2026-05-02

---

## Cosa è questo progetto

Un tool personale per cercare battle map D&D 5e gratuite, rilasciato come open source (GPL2). Indicizza mappe da fonti esterne con metadati strutturati (autore, licenza, tipo, tags) e permette di cercarle per tag, ambiente, licenza.

**Non è un concorrente di Lost Atlas** — è un progetto hobbistico con scope limitato. Vedi sezione "Posizionamento" in fondo.

### Caso d'uso

Stai scrivendo un modulo di un'avventura. Ti serve una taverna, un bosco, una cripta. Cerchi:

```bash
# Ricerca per tag
python search.py --env tavern --license free

# Ricerca testuale
python search.py --text "crypt altar"

# Download di una mappa specifica
python fetch.py dyson-logos/crypt-of-the-seven-sleepers

# Copia nell'avventura
cp ~/.dnd-map-index/maps/dyson-logos/crypt-of-the-seven-sleepers.png \
   ~/dungeonandragon/adventures/LoScettroDityr/03_RitornoACasa/maps/
```

---

## Fonti

Tutte le fonti sono definite in `sources.json` con i loro parametri. Ogni fonte ha un `status`:
- `active` — indicizzata e mantenuta
- `planned` — prossima da attivare
- `backlog` — definita ma non prioritaria

### Fonti identificate

| # | Fonte | Mappe | Licenza | Status |
|---|-------|-------|---------|--------|
| 1 | **Dyson Logos** (dysonlogos.blog) | ~1000 B&W | commercial-free, attribution | `active` |
| 2 | **Tom Cartos** (tomcartos.com) | ~500 watermarked | TOM license, attribution, no edit | `planned` |
| 3 | **2-Minute Tabletop** (2minutetabletop.com) | ~359 colore | CC BY-NC 4.0 | `active` |
| 4 | **Seafoot Games** (seafootgames.com) | ~200 | personal-free | `backlog` |
| 5 | **Dice Grimorium** (dicegrimorium.com) | ~100 | unknown (da verificare) | `backlog` |
| 6 | **Reddit r/battlemaps** | migliaia | variabile per post | `backlog` |
| 7 | **Forgotten Adventures** (forgotten-adventures.net) | ~50 | personal-free | `backlog` |

### Configurazione per fonte (`sources.json`)

Ogni comportamento che dipende dalla licenza/struttura della fonte è configurabile, non hardcoded:

| Campo | Valori | Descrizione |
|-------|--------|-------------|
| `status` | `active`, `planned`, `backlog` | Gli script ignorano le fonti non `active` |
| `thumbnail_policy` | `local`, `remote` | `local`: genera e committa thumbnail. `remote`: usa URL thumbnail del sito autore |
| `download_policy` | `direct`, `link_to_source` | `direct`: download dall'`image_url`. `link_to_source`: redirect alla pagina dell'autore |
| `indexing_method` | `scraper`, `manual_assisted` | `scraper`: script automatico. `manual_assisted`: script di supporto, compilazione manuale |

Aggiungere una nuova fonte = aggiungere un record in `sources.json` + (se `scraper`) scrivere lo script di indicizzazione.

**Fase 1**: solo Dyson Logos (`active`, `local`, `direct`, `scraper`).

---

## Modello dati

Ogni mappa è un record JSON:

```json
{
  "id": "dyson-logos-crypt-of-the-seven-sleepers",
  "title": "Crypt of the Seven Sleepers",
  "author": "Dyson Logos",
  "source_url": "https://dysonlogos.blog/2024/01/15/crypt-of-the-seven-sleepers/",
  "image_url": "https://dysonlogos.blog/wp-content/uploads/2024/01/crypt.png",
  "license": {
    "type": "commercial-free",
    "attribution": "Cartography by Dyson Logos"
  },
  "tags": ["crypt", "undead", "small"],
  "environment": "crypt",
  "map_type": "battlemap",
  "style": "bw-ink",
  "format": "png",
  "status": "ok",
  "date_indexed": "2026-05-02"
}
```

### Campi obbligatori

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `id` | string | Slug unico (`fonte-titolo-sluggato`) |
| `title` | string | Nome della mappa |
| `author` | string | Autore |
| `source_url` | string | URL pagina originale |
| `image_url` | string | URL diretto all'immagine |
| `license.type` | string | Categoria licenza |
| `license.attribution` | string | Testo di attribuzione richiesto |
| `tags` | string[] | Tag liberi per ricerca |
| `environment` | string | Tipo ambiente (vocabolario controllato) |
| `map_type` | string | `battlemap`, `regional`, `city`, `variant` |
| `status` | string | `ok`, `broken`, `removed`, `new` |
| `date_indexed` | string | Data indicizzazione |

### Campi opzionali

| Campo | Tipo | Descrizione |
|-------|------|-------------|
| `style` | string | `bw-ink`, `color-painted`, `color-digital` |
| `grid` | bool | Ha griglia visibile |
| `dimensions` | string | Dimensioni in quadretti (WxH) |
| `format` | string | `png`, `jpg`, `pdf` |
| `thumbnail` | string | Path thumbnail locale o URL remota |
| `description` | string | Descrizione testuale |
| `date_published` | string | Data pubblicazione originale |
| `last_checked` | string | Data ultimo rescan |
| `notes` | string | Note libere |

### Vocabolario — environment

```
dungeon, cave, crypt, sewer, mine,
tavern, inn, house, castle, temple, tower, shop,
forest, mountain, desert, swamp, coast, river, road, camp,
city, town, village, dock, market,
ship, underwater, planar, sky
```

### Tipi di licenza

| type | Download personale | Redistribuzione |
|------|-------------------|-----------------|
| `commercial-free` | ✅ | ✅ con attribution |
| `cc-by-nc` | ✅ | ❌ commerciale |
| `tom-open` | ✅ watermarked | ✅ con attribution, no edit |
| `personal-free` | ✅ | ❌ |
| `unknown` | ❌ | ❌ |

### Classificazione licenza per l'utente (UI)

| Etichetta | Tipi inclusi | Significato |
|-----------|-------------|-------------|
| 🟢 **Free** | `commercial-free`, `cc-by-nc`, `tom-open`, `personal-free` | Scaricabile e usabile (con attribuzione) |
| 🔴 **Solo link** | `unknown` | Non verificata — vai alla fonte |

---

## Struttura directory

```
dnd-map-index/                    # repo GPL2
├── index/                        # un JSON per fonte + manifest
│   ├── manifest.json             # lista file, conteggi, data aggiornamento
│   ├── dyson-logos.json
│   └── 2minute-tabletop.json
├── index.html                    # webapp (GitHub Pages)
├── sources.json                  # definizione fonti con configurazione
├── scripts/
│   ├── grab_core.py              # funzionalità comuni (pluggabile)
│   ├── grab-dyson.py             # plugin scraper Dyson Logos
│   ├── grab-2minute.py           # plugin scraper 2-Minute Tabletop
│   ├── search.py                 # ricerca CLI
│   ├── tag-assist.py             # tagger interattivo
│   └── rescan.py                 # manutenzione (autotag, colore, URL check)
├── tests/
│   └── test_all.py               # test di non regressione
├── docs/                         # documentazione
├── .gitignore
├── LICENSE                       # GPL2
└── README.md
```

Immagini full-size (mai nel repo):
```
~/.dnd-map-index/maps/            # configurabile via env var
└── dyson-logos/
    └── crypt-of-the-seven-sleepers.png
```

---

## Fasi di implementazione

### Fase 0 — Pianificazione ✅

- [x] Ricerca fonti e licenze
- [x] Modello dati e strategia
- [x] Analisi critica (C1-C9)
- [x] Posizionamento rispetto a Lost Atlas

### Fase 1 — MVP: Dyson Logos + CLI ✅

- [x] `sources.json` con tutte le 7 fonti configurate
- [x] `grab-dyson.py`: scrape → `index/dyson-logos.json` (650 mappe)
- [x] Auto-tagging da titolo (`guess_tags` in `grab_core.py`)
- [x] `search.py`: ricerca per tag, environment, licenza, autore, testo libero
- [x] `README.md` con descrizione onesta e raccomandazione Lost Atlas
- [ ] `fetch.py`: download on-demand (non ancora implementato)

### Fase 2 — Fonti aggiuntive + architettura pluggabile ✅ (parziale)

- [x] `grab_core.py`: funzionalità comuni (slugify, guess_tags, fetch cached, save + manifest)
- [x] Architettura pluggabile: ogni fonte ha `grab-<source>.py` che importa da `grab_core`
- [x] `grab-2minute.py`: 2-Minute Tabletop attivato (359 mappe)
- [x] `index/manifest.json`: generato automaticamente, lista file + conteggi
- [x] Merge con dati esistenti al re-grab (preserva tag manuali, rescan data)
- [ ] Attivare Tom Cartos
- [ ] Attivare Seafoot Games, Dice Grimorium, Reddit, Forgotten Adventures

### Fase 3 — Rescan ✅

- [x] `rescan.py` unificato: default processa N mappe con tutti i check pendenti
- [x] Check incrementali: auto-tag (se vuoto), colore (se non scansionato), URL (sempre)
- [x] Flag singoli (`--autotag`, `--color`, `--check-urls`) forzano il check anche se già fatto
- [x] `rescan-status.json`: stato machine-readable aggiornato ad ogni esecuzione
- [x] Policy broken → removed documentata (2 rescan consecutivi)

### Fase 4 — Web app ✅

- [x] Sito statico su GitHub Pages (`index.html` nella root)
- [x] Caricamento dinamico da `manifest.json` (supporta fonti multiple)
- [x] Griglia con thumbnail remote (lazy loading)
- [x] Filtri: environment, autore/fonte, licenza, B&W/colore, preview, testo libero
- [x] Paginazione (24 mappe per pagina)
- [x] About con scopi, limiti, link progetti fratelli, contatto copyright
- [x] Infobar con conteggio mappe, numero fonti, data ultimo aggiornamento
- [x] Tab fonti apribile con licenze e policy

### Fase 5 — Ricerca semantica (futura, non nel MVP)

- [ ] Embedding descrizioni/tag
- [ ] Endpoint API serverless (Cloudflare Workers o Vercel)
- [ ] Prerequisito: tagging/descrizioni sufficientemente ricche

### Fase 6 — Integrazione dungeonandragon (futura)

- [ ] Script che legge il .md di un modulo e suggerisce mappe dall'indice
- [ ] Copia in `adventures/*/maps/` con file `.md` di attribuzione

---

## Decisioni architetturali (C1-C9)

| # | Critica | Decisione |
|---|---------|-----------|
| C1 | Thumbnail legali | Locali solo per fonti con licenza esplicita (`thumbnail_policy` per fonte) |
| C2 | Download proxy | Download diretto solo per fonti con licenza esplicita (`download_policy` per fonte) |
| C3 | Scraping fragile | Semi-manuale per la maggior parte, scraper solo per fonti stabili (`indexing_method` per fonte) |
| C4 | Stima ottimistica | Campo `map_type` per filtrare. Numero reale inferiore è ok |
| C5 | Tagging collo di bottiglia | 20 mappe manuali per validare, poi valutare LLM |
| C6 | Ricerca semantica complessa | Rimandata. Ricerca per tag nel MVP. Lost Atlas come alternativa |
| C7 | Scalabilità web app | Thumbnail remote + lazy loading. Architettura non preclude crescita |
| C8 | Mappe sparite | 2 rescan broken → `removed`, nascosta, thumbnail rimossa |
| C9 | Priorità fonti | Solo Dyson Logos fase 1. Altre in `sources.json` con status `planned`/`backlog` |

---

## Posizionamento

### Lost Atlas — alternativa commerciale raccomandata

[Lost Atlas](https://lostatlas.co) è un motore di ricerca con 5000+ battle map, ricerca per keyword, filtri, Discord bot, tier premium ($5/mese). **Se cerchi un servizio pronto all'uso, completo e mantenuto professionalmente, usa Lost Atlas.**

### Perché dnd-map-index esiste

| | Lost Atlas | dnd-map-index |
|-|------------|---------------|
| Mappe | 5000+ | poche centinaia |
| Manutenzione | team dedicato | hobbistico |
| Filtro licenza | ❌ | ✅ |
| Open source | ❌ | ✅ GPL2 |
| Offline | ❌ | ✅ |
| Integrabile | ❌ | ✅ CLI + script |
| Costo | free + $5/mese | gratis |

---

## Rischi

| Rischio | Impatto | Mitigazione |
|---------|---------|-------------|
| Violazione copyright | Alto | Download solo con licenza verificata; `unknown` blocca download |
| Scraper si rompe | Medio | Semi-manuale per la maggior parte; scraper solo Dyson Logos |
| URL spariscono | Medio | `rescan.py`; policy `broken` → `removed` |
| Spazio disco | Basso | Solo metadati+thumbnail nel repo; full-size on-demand |
| Rate limiting | Medio | Delay tra richieste; rispettare robots.txt |

---

## Dipendenze

- **Python 3.8+**
- **requests** — HTTP client
- **beautifulsoup4** — parsing HTML (solo per scraper)
- **Pillow** — generazione thumbnail (solo per fonti `thumbnail_policy: local`)
