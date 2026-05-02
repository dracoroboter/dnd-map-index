# rescan.py — Incremental index maintenance

> ⚠️ This is an auto-translated version of [rescan.md](rescan.md). It may be outdated. The Italian version is the source of truth.

Script for index maintenance. Works in small batches to avoid overloading source servers.

## Operations

### Color detection (B&W vs color)

Downloads the thumbnail of N unscanned maps and determines whether they are black & white or color by analyzing pixel saturation.

```bash
python3 scripts/rescan.py              # default: 5 maps
python3 scripts/rescan.py --color 20   # 20 maps
```

Maps are chosen randomly among those not yet scanned. Each run advances progress. The `style` field is updated to `bw-ink` or `color`, and `style_scanned` is set to `true`.

### URL check

HEAD request on `source_url` to verify pages are still reachable. Checks maps with the oldest `last_checked`.

```bash
python3 scripts/rescan.py --check-urls      # default: 10 maps
python3 scripts/rescan.py --check-urls 50   # 50 maps
```

If a URL returns 404 or times out, the `status` field becomes `broken`. After 2 consecutive `broken` rescans, the map should be marked `removed` (manually for now).

### Statistics

```bash
python3 scripts/rescan.py --stats
```

## Status file

Each run writes `rescan-status.json` in the repo root. Format:

```json
{
  "last_run": "2026-05-02T16:53:12",
  "operation": "color",
  "sources": {
    "dyson-logos": {
      "total": 650,
      "color_scanned": 8,
      "color_bw": 8,
      "color_color": 0,
      "url_checked": 0,
      "url_broken": 0,
      "tagged": 650,
      "with_thumbnail": 650
    }
  },
  "details": {
    "scanned": 3
  }
}
```

Fields:
- `last_run` — ISO timestamp of last run
- `operation` — operation type (`color`, `check-urls`)
- `sources.<name>` — per-source statistics
- `details` — parameters of the last run
