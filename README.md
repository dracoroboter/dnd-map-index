# dnd-map-index

> 🇬🇧 [English version (auto-translated)](README.en.md)

**Versione**: 0.1.0 — 2026-05-02

Indice ricercabile di battle map D&D 5e gratuite, con metadati strutturati (autore, licenza, tipo, tags).

**Stato**: MVP — 650 mappe Dyson Logos indicizzate, 20 taggate, ricerca CLI funzionante.

---

## Cosa fa

Indicizza mappe da fonti esterne e permette di cercarle per ambiente, tag, licenza, testo libero. Le immagini non sono nel repo — solo metadati JSON e link alle fonti originali. Download on-demand delle singole mappe in una directory locale.

## Cosa NON fa

Non è un servizio completo. È un tool personale con scope limitato. Se cerchi un motore di ricerca pronto all'uso con 5000+ mappe, usa **[Lost Atlas](https://lostatlas.co)** — è migliore sotto ogni aspetto tranne che non è open source e non filtra per licenza.

## Perché esiste

| | Lost Atlas | dnd-map-index |
|-|------------|---------------|
| Mappe | 5000+ | ~650 (Dyson Logos) |
| Filtro licenza | ❌ | ✅ |
| Open source | ❌ | ✅ GPL2 |
| Offline | ❌ | ✅ |
| Integrabile con script | ❌ | ✅ |

---

## Interfaccia web

Il sito è disponibile su **[dracoroboter.github.io/dnd-map-index](https://dracoroboter.github.io/dnd-map-index/)** — servito da GitHub Pages direttamente dal repo.

Ricerca client-side su `index.html` nella root del repo. Filtri per ambiente, licenza, testo libero. Nessun backend.

### Setup GitHub Pages (una tantum)

1. GitHub → repo → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main**, folder: **/ (root)**
4. Save — il sito è attivo dopo qualche minuto

I push successivi aggiornano il sito automaticamente.

### Sviluppo locale

```bash
cd ~/dnd-map-index
python3 -m http.server 8080
# apri http://localhost:8080
```

---

## Uso rapido (CLI)

```bash
# Statistiche indice
python3 scripts/search.py --stats

# Cerca per ambiente
python3 scripts/search.py --env tavern

# Cerca per testo nel titolo
python3 scripts/search.py --text crypt

# Cerca solo mappe taggate
python3 scripts/search.py --env temple --tagged-only

# Cerca per licenza
python3 scripts/search.py --license free -n 10

# Taggare mappe interattivamente (20 diverse per tipo)
python3 scripts/tag-assist.py --pick 20 --diverse

# Rieseguire lo scraper (aggiorna l'indice)
python3 scripts/grab-dyson.py
```

## Struttura

```
dnd-map-index/
├── index/                  # un JSON per fonte
│   └── dyson-logos.json    # 650 mappe
├── sources.json            # configurazione fonti (licenze, policy)
├── scripts/
│   ├── grab-dyson.py       # scraper Dyson Logos
│   ├── tag-assist.py       # tagger interattivo
│   └── search.py           # ricerca CLI
├── docs/
│   └── PlanBook.md         # piano di sviluppo completo
└── .gitignore
```

## Fonti

| Fonte | Mappe | Licenza | Status |
|-------|-------|---------|--------|
| **Dyson Logos** | ~650 | commercial-free (attribution) | ✅ active |
| Tom Cartos | ~500 | TOM license (attribution, no edit) | planned |
| 2-Minute Tabletop | ~300 | CC BY-NC 4.0 | planned |
| Seafoot Games | ~200 | personal-free | backlog |
| Dice Grimorium | ~100 | da verificare | backlog |
| Reddit r/battlemaps | variabile | variabile | backlog |
| Forgotten Adventures | ~50 | personal-free | backlog |

Ogni fonte è configurata in `sources.json` con policy per thumbnail, download e metodo di indicizzazione. Aggiungere una fonte = aggiungere un record + (opzionalmente) uno script.

## Dipendenze

- Python 3.8+
- `requests`, `beautifulsoup4` — per gli scraper
- `Pillow` — per generazione thumbnail (futuro)

```bash
pip install requests beautifulsoup4
```

## Progetti correlati

Questo progetto fa parte di una famiglia di tool per D&D 5e:

- **[dnd-maps](https://github.com/dracoroboter/dnd-maps)** — toolchain per generare e renderizzare mappe D&D (generazione procedurale, renderer SVG multi-stile, sistema di arredamento DDL/RTL)
- **[dnd-generator](https://github.com/dracoroboter/dnd-generator)** — avventure D&D 5e homebrew (usa le mappe indicizzate qui come riferimento visivo)

## Licenza

| contenuto | licenza |
|-----------|---------|
| Script e software | [GNU General Public License v2 (GPLv2)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) |
| Metadati nell'indice | Dati fattuali (titoli, URL, licenze) — non soggetti a copyright |
| Immagini delle mappe | **NON incluse nel repo** — proprietà dei rispettivi autori, vedi campo `license` in ogni record |

## Autore

**dracoroboter**

Sono "dracoroboter" in rete dalla fine degli anni '90 del secolo scorso. Faccio il programmatore di lavoro, ho iniziato a fare il master nel 2024 e quindi sono ancora un niubbo. Se volete contattarmi potete usare la mail dracoroboter(at)gmail.com.
