# dnd-map-index

> 🇮🇹 [Versione italiana (originale)](README.md)
>
> ⚠️ This is an auto-translated version of the Italian README. It may be outdated. The Italian version is the source of truth.

**Version**: 0.2.0 — 2026-05-02

A searchable index of free D&D 5e battle maps, with structured metadata (author, license, type, tags).

**Status**: 1009 maps indexed from 2 sources (Dyson Logos + 2-Minute Tabletop), CLI search and webapp working.

---

## What it does

Indexes maps from external sources and lets you search by environment, tag, license, free text. Images are not in the repo — only JSON metadata and links to original sources. On-demand download of individual maps to a local directory.

## What it does NOT do

This is not a complete service. It's a personal tool with limited scope. If you need a ready-to-use search engine with 5000+ maps, use **[Lost Atlas](https://lostatlas.co)** — it's better in every way except it's not open source and doesn't filter by license.

## Why it exists

| | Lost Atlas | dnd-map-index |
|-|------------|---------------|
| Maps | 5000+ | ~1009 (2 sources) |
| License filter | ❌ | ✅ |
| Open source | ❌ | ✅ GPL2 |
| Offline | ❌ | ✅ |
| Scriptable | ❌ | ✅ |

---

## Web interface

The site is available at **[dracoroboter.github.io/dnd-map-index](https://dracoroboter.github.io/dnd-map-index/)** — served by GitHub Pages directly from the repo.

Client-side search on `index.html` in the repo root. Filters by environment, license, free text. No backend.

### GitHub Pages setup (one-time)

1. GitHub → repo → Settings → Pages
2. Source: **Deploy from a branch**
3. Branch: **main**, folder: **/ (root)**
4. Save — site is live after a few minutes

Subsequent pushes update the site automatically.

### Local development

```bash
cd ~/dnd-map-index
python3 -m http.server 8080
# open http://localhost:8080
```

---

## Quick start (CLI)

```bash
# Index statistics
python3 scripts/search.py --stats

# Search by environment
python3 scripts/search.py --env tavern

# Search by title text
python3 scripts/search.py --text crypt

# Search by license
python3 scripts/search.py --license free -n 10

# Search by author/source
python3 scripts/search.py --author "Dyson Logos"

# Interactive tagging (20 diverse maps)
python3 scripts/tag-assist.py --pick 20 --diverse

# Re-run scrapers (updates the index)
python3 scripts/grab-dyson.py
python3 scripts/grab-2minute.py

# Auto-tag untagged maps
python3 scripts/rescan.py --autotag

# Detect B&W vs color (5 maps at a time)
python3 scripts/rescan.py --color 5

# Non-regression tests
python3 tests/test_all.py
```

## Structure

```
dnd-map-index/
├── index/                  # one JSON per source + manifest
│   ├── manifest.json       # file list, counts, update date
│   ├── dyson-logos.json    # 650 maps
│   └── 2minute-tabletop.json # 359 maps
├── index.html              # webapp (GitHub Pages)
├── sources.json            # source configuration (licenses, policies)
├── scripts/
│   ├── grab_core.py        # shared utilities (pluggable)
│   ├── grab-dyson.py       # Dyson Logos scraper plugin
│   ├── grab-2minute.py     # 2-Minute Tabletop scraper plugin
│   ├── search.py           # CLI search
│   ├── tag-assist.py       # interactive tagger
│   └── rescan.py           # maintenance (autotag, color, URL check)
├── tests/
│   └── test_all.py         # non-regression tests
├── docs/                   # documentation (Italian, English translations)
└── .gitignore
```

### Pluggable architecture

Each source has a `grab-<source>.py` script that imports shared utilities from `grab_core.py` (slugify, guess_tags, cached fetch, index save + manifest). To add a source: create a new `grab-<source>.py` + add a record in `sources.json`.

## Sources

| Source | Maps | License | Status |
|--------|------|---------|--------|
| **Dyson Logos** | ~650 | commercial-free (attribution) | ✅ active |
| **2-Minute Tabletop** | ~359 | CC BY-NC 4.0 | ✅ active |
| Tom Cartos | ~500 | TOM license (attribution, no edit) | planned |
| Seafoot Games | ~200 | personal-free | backlog |
| Dice Grimorium | ~100 | to verify | backlog |
| Reddit r/battlemaps | variable | variable | backlog |
| Forgotten Adventures | ~50 | personal-free | backlog |

Each source is configured in `sources.json` with policies for thumbnails, downloads, and indexing method. Adding a source = adding a record + (optionally) a script.

## Next steps

- [ ] Activate **Tom Cartos** (~500 maps, TOM license) — `grab-tomcartos.py`
- [ ] Activate **Seafoot Games** (~200 maps, personal-free) — `grab-seafoot.py`
- [ ] Activate **Dice Grimorium** (~100 maps, license to verify) — `grab-dicegrimorium.py`
- [ ] Manual curation **Reddit r/battlemaps** — select posts with clear license
- [ ] Activate **Forgotten Adventures** (~50 maps) — `grab-forgottenadv.py`
- [ ] Complete B&W/color rescan across all sources
- [ ] Semantic search (future)
- [ ] Integration with `dungeonandragon` project (future)

## Dependencies

- Python 3.8+
- `requests`, `beautifulsoup4` — for scrapers
- `Pillow` — for thumbnail generation (future)

```bash
pip install requests beautifulsoup4
```

## Related projects

This project is part of a family of D&D 5e tools:

- **[dnd-maps](https://github.com/dracoroboter/dnd-maps)** — toolchain for generating and rendering D&D maps (procedural generation, multi-style SVG renderers, DDL/RTL furnishing system)
- **[dnd-generator](https://github.com/dracoroboter/dnd-generator)** — homebrew D&D 5e adventures (uses maps indexed here as visual reference)

## License

| content | license |
|---------|---------|
| Scripts and software | [GNU General Public License v2 (GPLv2)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) |
| Index metadata | Factual data (titles, URLs, licenses) — not subject to copyright |
| Map images | **NOT included in the repo** — property of their respective authors, see `license` field in each record |

## Author

**dracoroboter**

I've been "dracoroboter" online since the late '90s. I'm a programmer by trade, started DMing in 2024, so I'm still very much a noob.

- 📧 dracoroboter(at)gmail.com
- 🎲 [dracoroboter.itch.io/dungeon-and-dragons-tools](https://dracoroboter.itch.io/dungeon-and-dragons-tools)
- 💬 [GitHub Discussions](https://github.com/dracoroboter/dnd-map-index/discussions/1)
