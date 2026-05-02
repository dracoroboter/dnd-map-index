# rescan.py — Incremental index maintenance

> ⚠️ This is an auto-translated version of [rescan.md](rescan.md). It may be outdated. The Italian version is the source of truth.

Script for index maintenance. Works in small batches to avoid overloading source servers.

## Default behavior (no flags)

Processes N maps (default 5) performing **all pending checks**:

1. **Auto-tag** — only if `tags` is empty
2. **Color detection** — only if `style_scanned` is absent
3. **URL check** — always (HEAD request)

```bash
python3 scripts/rescan.py          # 5 maps
python3 scripts/rescan.py 20       # 20 maps
```

Each run advances progress. Maps are chosen randomly for variety.

## Single flags (force the check)

Single flags **force** the check even on already-processed maps — useful for rescanning after changes.

### `--autotag` — Force re-tag on all maps

```bash
python3 scripts/rescan.py --autotag
```

Recalculates tags and environment from `guess_tags(title)` for **all** maps, overwriting existing tags.

### `--color N` — Force color detection

```bash
python3 scripts/rescan.py --color 20
```

Downloads the thumbnail of N maps (even already scanned) and determines B&W vs color.

### `--check-urls N` — Force URL check

```bash
python3 scripts/rescan.py --check-urls 50
```

HEAD request on N maps (even already checked). If 404/timeout → `status: broken`.

### `--stats` — Statistics

```bash
python3 scripts/rescan.py --stats
```

## Status file

Each run writes `rescan-status.json` in the repo root. Format:

```json
{
  "last_run": "2026-05-02T17:25:00",
  "operation": "rescan",
  "sources": {
    "dyson-logos": {
      "total": 650,
      "tagged": 650,
      "color_scanned": 3,
      "url_checked": 3,
      "url_broken": 0,
      "with_thumbnail": 650
    }
  },
  "details": { "processed": 5 }
}
```
