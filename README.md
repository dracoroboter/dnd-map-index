# dnd-map-index

> 🇬🇧 [English version (auto-translated)](README.en.md)

**Versione**: 0.2.0 — 2026-05-02

Indice ricercabile di battle map D&D 5e gratuite, con metadati strutturati (autore, licenza, tipo, tags).

**Stato**: 1508 mappe indicizzate da 4 fonti (Dyson Logos + 2-Minute Tabletop + Tom Cartos + Seafoot Games), ricerca CLI e webapp funzionanti.

---

## Cosa fa

Indicizza mappe da fonti esterne e permette di cercarle per ambiente, tag, licenza, testo libero. Le immagini non sono nel repo — solo metadati JSON e link alle fonti originali. Download on-demand delle singole mappe in una directory locale.

## Cosa NON fa

Non è un servizio completo. È un tool personale con scope limitato. Se cerchi un motore di ricerca pronto all'uso con 5000+ mappe, usa **[Lost Atlas](https://lostatlas.co)** — è migliore sotto ogni aspetto tranne che non è open source e non filtra per licenza.

## Perché esiste

| | Lost Atlas | dnd-map-index |
|-|------------|---------------|
| Mappe | 5000+ | ~1508 (4 fonti) |
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

### Analytics

Il sito usa [GoatCounter](https://www.goatcounter.com) per statistiche anonime sulle visite. Nessun cookie, nessun tracciamento personale, GDPR-friendly. Dashboard pubblica: [dracoroboter.goatcounter.com](https://dracoroboter.goatcounter.com).

---

## Uso rapido (CLI)

```bash
# Statistiche indice
python3 scripts/search.py --stats

# Cerca per ambiente
python3 scripts/search.py --env tavern

# Cerca per testo nel titolo
python3 scripts/search.py --text crypt

# Cerca per licenza
python3 scripts/search.py --license free -n 10

# Cerca per autore/fonte
python3 scripts/search.py --author "Dyson Logos"

# Taggare mappe interattivamente (20 diverse per tipo)
python3 scripts/tag-assist.py --pick 20 --diverse

# Rieseguire gli scraper (aggiorna l'indice)
python3 scripts/grab-dyson.py
python3 scripts/grab-2minute.py
python3 scripts/grab-tomcartos.py
python3 scripts/grab-seafoot.py

# Auto-taggare mappe senza tag
python3 scripts/rescan.py --autotag

# Rilevamento B&W vs colore (5 mappe alla volta)
python3 scripts/rescan.py --color 5

# Test di non regressione
python3 tests/test_all.py
```

## Struttura

```
dnd-map-index/
├── index/                  # un JSON per fonte + manifest
│   ├── manifest.json       # lista file, conteggi, data aggiornamento
│   ├── dyson-logos.json    # 650 mappe
│   ├── 2minute-tabletop.json # 359 mappe
│   ├── tom-cartos.json    # 289 mappe
│   └── seafoot-games.json # 210 mappe
├── index.html              # webapp (GitHub Pages)
├── sources.json            # configurazione fonti (licenze, policy)
├── scripts/
│   ├── grab_core.py        # funzionalità comuni (pluggabile)
│   ├── grab-dyson.py       # plugin scraper Dyson Logos
│   ├── grab-2minute.py     # plugin scraper 2-Minute Tabletop
│   ├── grab-tomcartos.py   # plugin scraper Tom Cartos
│   ├── grab-seafoot.py    # plugin scraper Seafoot Games
│   ├── search.py           # ricerca CLI
│   ├── tag-assist.py       # tagger interattivo
│   └── rescan.py           # manutenzione (autotag, colore, URL check)
├── tests/
│   └── test_all.py         # test di non regressione
├── docs/                   # documentazione (italiano, traduzioni inglesi)
└── .gitignore
```

### Architettura pluggabile

Ogni fonte ha uno script `grab-<source>.py` che importa da `grab_core.py` le funzionalità comuni (slugify, guess_tags, fetch con cache, salvataggio indice + manifest). Per aggiungere una fonte: creare un nuovo `grab-<source>.py` + aggiungere un record in `sources.json`.

## Fonti

| Fonte | Mappe | Licenza | Status |
|-------|-------|---------|--------|
| **Dyson Logos** | ~650 | commercial-free (attribution) | ✅ active |
| **2-Minute Tabletop** | ~359 | CC BY-NC 4.0 | ✅ active |
| **Tom Cartos** | ~289 | TOM license (attribution, no edit) | ✅ active |
| **Seafoot Games** | ~210 | personal-free | ✅ active |
| Dice Grimorium | ~100 | da verificare | backlog |
| Reddit r/battlemaps | variabile | variabile | backlog |
| Forgotten Adventures | ~50 | personal-free | backlog |

Ogni fonte è configurata in `sources.json` con policy per thumbnail, download e metodo di indicizzazione. Aggiungere una fonte = aggiungere un record + (opzionalmente) uno script.

## Prossimi passi

- [x] ~~Attivare **Tom Cartos** (~289 mappe, TOM license) — `grab-tomcartos.py`~~
- [x] ~~Attivare **Seafoot Games** (~210 mappe, personal-free) — `grab-seafoot.py`~~
- [ ] Attivare **Dice Grimorium** (~100 mappe, licenza da verificare) — `grab-dicegrimorium.py`
- [ ] Curazione manuale **Reddit r/battlemaps** — selezione post con licenza chiara
- [ ] Attivare **Forgotten Adventures** (~50 mappe) — `grab-forgottenadv.py`
- [ ] Completare rescan colore B&W/color su tutte le fonti
- [ ] Ricerca semantica (futura)
- [ ] Integrazione con progetto `dungeonandragon` (futura)

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
