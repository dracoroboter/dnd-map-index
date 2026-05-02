# dnd-map-index

> 🇮🇹 [Versione italiana (originale)](README.md)
>
> ⚠️ This is an auto-translated version of the Italian README. It may be outdated. The Italian version is the source of truth.

**Version**: 0.1.0 — 2026-05-02

A searchable index of free D&D 5e battle maps, with structured metadata (author, license, type, tags).

**Status**: MVP — 650 Dyson Logos maps indexed, 20 tagged, CLI search working.

---

## What it does

Indexes maps from external sources and lets you search by environment, tag, license, free text. Images are not in the repo — only JSON metadata and links to original sources. On-demand download of individual maps to a local directory.

## What it does NOT do

This is not a complete service. It's a personal tool with limited scope. If you need a ready-to-use search engine with 5000+ maps, use **[Lost Atlas](https://lostatlas.co)** — it's better in every way except it's not open source and doesn't filter by license.

## Why it exists

| | Lost Atlas | dnd-map-index |
|-|------------|---------------|
| Maps | 5000+ | ~650 (Dyson Logos) |
| License filter | ❌ | ✅ |
| Open source | ❌ | ✅ GPL2 |
| Offline | ❌ | ✅ |
| Scriptable | ❌ | ✅ |

---

## Quick start

```bash
# Index statistics
python3 scripts/search.py --stats

# Search by environment
python3 scripts/search.py --env tavern

# Search by title text
python3 scripts/search.py --text crypt

# Search tagged maps only
python3 scripts/search.py --env temple --tagged-only

# Search by license
python3 scripts/search.py --license free -n 10

# Interactive tagging (20 diverse maps)
python3 scripts/tag-assist.py --pick 20 --diverse

# Re-run scraper (updates the index)
python3 scripts/grab-dyson.py
```

## Structure

```
dnd-map-index/
├── index/                  # one JSON per source
│   └── dyson-logos.json    # 650 maps
├── sources.json            # source configuration (licenses, policies)
├── scripts/
│   ├── grab-dyson.py       # Dyson Logos scraper
│   ├── tag-assist.py       # interactive tagger
│   └── search.py           # CLI search
├── docs/
│   └── PlanBook.md         # development plan (Italian only)
└── .gitignore
```

## Sources

| Source | Maps | License | Status |
|--------|------|---------|--------|
| **Dyson Logos** | ~650 | commercial-free (attribution) | ✅ active |
| Tom Cartos | ~500 | TOM license (attribution, no edit) | planned |
| 2-Minute Tabletop | ~300 | CC BY-NC 4.0 | planned |
| Seafoot Games | ~200 | personal-free | backlog |
| Dice Grimorium | ~100 | to verify | backlog |
| Reddit r/battlemaps | variable | variable | backlog |
| Forgotten Adventures | ~50 | personal-free | backlog |

Each source is configured in `sources.json` with policies for thumbnails, downloads, and indexing method. Adding a source = adding a record + (optionally) a script.

## Dependencies

- Python 3.8+
- `requests`, `beautifulsoup4` — for scrapers
- `Pillow` — for thumbnail generation (future)

```bash
pip install requests beautifulsoup4
```

## Related projects

- **[dnd-maps](https://github.com/dracoroboter/dnd-maps)** — toolchain for generating and rendering D&D maps
- **[dnd-generator](https://github.com/dracoroboter/dnd-generator)** — D&D adventures (uses maps indexed here)

## License

| content | license |
|---------|---------|
| Scripts and software | [GNU General Public License v2 (GPLv2)](https://www.gnu.org/licenses/old-licenses/gpl-2.0.html) |
| Index metadata | Factual data (titles, URLs, licenses) — not subject to copyright |
| Map images | **NOT included in the repo** — property of their respective authors, see `license` field in each record |

## Author

**dracoroboter** — `dracoroboter(at)gmail.com`
