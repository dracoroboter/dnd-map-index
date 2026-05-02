# rescan.py — Manutenzione incrementale dell'indice

> 🇬🇧 [English version (auto-translated)](rescan.en.md)

Script per la manutenzione dell'indice. Lavora in batch piccoli per non sovraccaricare i server delle fonti.

## Operazioni

### Rilevamento colore (B&W vs color)

Scarica la thumbnail di N mappe non ancora scansionate e determina se sono in bianco/nero o a colori analizzando la saturazione dei pixel.

```bash
python3 scripts/rescan.py              # default: 5 mappe
python3 scripts/rescan.py --color 20   # 20 mappe
```

Le mappe vengono scelte casualmente tra quelle non ancora scansionate. Ogni esecuzione avanza il progresso. Il campo `style` viene aggiornato a `bw-ink` o `color`, e `style_scanned` viene impostato a `true`.

### Verifica URL

HEAD request su `source_url` per verificare che le pagine siano ancora raggiungibili. Controlla le mappe con `last_checked` più vecchio.

```bash
python3 scripts/rescan.py --check-urls      # default: 10 mappe
python3 scripts/rescan.py --check-urls 50   # 50 mappe
```

Se una URL ritorna 404 o timeout, il campo `status` diventa `broken`. Dopo 2 rescan consecutivi `broken`, la mappa va marcata `removed` (manualmente per ora).

### Statistiche

```bash
python3 scripts/rescan.py --stats
```

## File di stato

Ogni esecuzione scrive `rescan-status.json` nella root del repo. Formato:

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

Campi:
- `last_run` — timestamp ISO dell'ultima esecuzione
- `operation` — tipo di operazione (`color`, `check-urls`)
- `sources.<nome>` — statistiche per fonte
- `details` — parametri dell'ultima esecuzione
