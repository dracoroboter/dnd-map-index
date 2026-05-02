# tag-assist.py — Interactive map tagging

> ⚠️ This is an auto-translated version of [tag-assist.md](tag-assist.md). It may be outdated. The Italian version is the source of truth.

Interactive script for assigning tags and environment to maps in the index. Shows one map at a time with automatic suggestions from the title; the user confirms or edits.

## Usage

```bash
# Tag 20 maps diverse by environment type
python3 scripts/tag-assist.py --pick 20 --diverse

# Tag 10 untagged maps
python3 scripts/tag-assist.py --pick 10

# Tag all untagged maps (interactive)
python3 scripts/tag-assist.py
```

**Note**: this script requires interactive input — run it directly from a terminal, not from an automated tool.

## Commands during tagging

| Command | Action |
|---------|--------|
| `ENTER` | Accept suggested tags and environment |
| `e` | Edit tags manually (comma-separated) |
| `v` | Edit environment |
| `s` | Skip this map |
| `q` | Quit and save |

## How auto-suggestion works

The script analyzes the map title and looks for known keywords:

| Title keyword | Suggested tags | Environment |
|--------------|----------------|-------------|
| crypt, tomb, barrow | crypt/tomb, undead | crypt |
| cave, cavern, grotto | cave/cavern, natural | cave |
| tavern, inn, alehouse | tavern/inn, social | tavern/inn |
| temple, shrine, church | temple/shrine, religious | temple |
| tower, spire | tower, vertical | tower |
| castle, keep, fortress | castle/keep, fortification | castle |
| manor, estate, house | manor/estate, building | house |
| sewer | sewer, urban | sewer |
| village, town, city | settlement | village/town/city |

If no keyword is recognized, the default environment is `dungeon`.

## `--diverse` option

Selects maps spread across as many different environments as possible, to validate the vocabulary on different map types.

## Modified files

The script directly updates `index/<source>.json`. Fields modified per map:
- `tags` — tag list
- `environment` — environment type
- `status` — set to `ok` after tagging
