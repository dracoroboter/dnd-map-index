# tag-assist.py — Tagging interattivo delle mappe

> 🇬🇧 [English version (auto-translated)](tag-assist.en.md)

Script interattivo per assegnare tag e environment alle mappe nell'indice. Mostra una mappa alla volta con suggerimenti automatici dal titolo, l'utente conferma o corregge.

## Uso

```bash
# Taggare 20 mappe diverse per tipo di ambiente
python3 scripts/tag-assist.py --pick 20 --diverse

# Taggare 10 mappe qualsiasi non ancora taggate
python3 scripts/tag-assist.py --pick 10

# Taggare tutte le mappe non taggate (interattivo)
python3 scripts/tag-assist.py
```

**Nota**: lo script richiede input interattivo — va lanciato direttamente dal terminale, non da un tool automatico.

## Comandi durante il tagging

| Comando | Azione |
|---------|--------|
| `ENTER` | Accetta tag e environment suggeriti |
| `e` | Modifica i tag manualmente (inserire separati da virgola) |
| `v` | Modifica l'environment |
| `s` | Salta questa mappa |
| `q` | Esci e salva |

## Come funziona il suggerimento automatico

Lo script analizza il titolo della mappa e cerca keyword note:

| Keyword nel titolo | Tag suggeriti | Environment |
|-------------------|---------------|-------------|
| crypt, tomb, barrow | crypt/tomb, undead | crypt |
| cave, cavern, grotto | cave/cavern, natural | cave |
| tavern, inn, alehouse | tavern/inn, social | tavern/inn |
| temple, shrine, church | temple/shrine, religious | temple |
| tower, spire | tower, vertical | tower |
| castle, keep, fortress | castle/keep, fortification | castle |
| manor, estate, house | manor/estate, building | house |
| sewer | sewer, urban | sewer |
| village, town, city | settlement | village/town/city |

Se nessuna keyword viene riconosciuta, l'environment di default è `dungeon`.

## Opzione `--diverse`

Seleziona mappe distribuite tra il maggior numero possibile di ambienti diversi, per validare il vocabolario su tipi diversi di mappe.

## File modificati

Lo script aggiorna direttamente `index/<fonte>.json`. I campi modificati per ogni mappa sono:
- `tags` — lista di tag
- `environment` — tipo di ambiente
- `status` — impostato a `ok` dopo il tagging
