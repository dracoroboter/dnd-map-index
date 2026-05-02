# rescan.py — Manutenzione incrementale dell'indice

> 🇬🇧 [English version (auto-translated)](rescan.en.md)

Script per la manutenzione dell'indice. Lavora in batch piccoli per non sovraccaricare i server delle fonti.

## Comportamento default (senza flag)

Processa N mappe (default 5) facendo **tutti i controlli pendenti**:

1. **Auto-tag** — solo se `tags` è vuoto
2. **Rilevamento colore** — solo se `style_scanned` è assente
3. **Verifica URL** — sempre (HEAD request)

```bash
python3 scripts/rescan.py          # 5 mappe
python3 scripts/rescan.py 20       # 20 mappe
```

Ogni esecuzione avanza il progresso. Le mappe vengono scelte casualmente per varietà.

## Flag singoli (forzano il controllo)

I flag singoli **forzano** il check anche su mappe già processate — utile per riscansionare dopo modifiche.

### `--autotag` — Forza re-tag su tutte le mappe

```bash
python3 scripts/rescan.py --autotag
```

Ricalcola tag e environment da `guess_tags(title)` per **tutte** le mappe, sovrascrivendo i tag esistenti.

### `--color N` — Forza rilevamento colore

```bash
python3 scripts/rescan.py --color 20
```

Scarica la thumbnail di N mappe (anche già scansionate) e determina B&W vs colore.

### `--check-urls N` — Forza verifica URL

```bash
python3 scripts/rescan.py --check-urls 50
```

HEAD request su N mappe (anche già verificate). Se 404/timeout → `status: broken`.

### `--stats` — Statistiche

```bash
python3 scripts/rescan.py --stats
```

## File di stato

Ogni esecuzione scrive `rescan-status.json` nella root del repo. Formato:

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
