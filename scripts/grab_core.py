"""Core utilities for grab-* plugins.

Each grab-<source>.py plugin implements:
  - extract_maps(html_or_data) → list of map dicts
  - fetch_pages() → list of HTML strings (handles pagination, caching)

The plugin calls grab_core functions for:
  - slugify(text) → URL-safe slug
  - guess_tags(title) → (tags, environment)
  - make_entry(source_id, title, source_url, ...) → map dict with defaults
  - fetch_cached(url, cache_name) → HTML string with caching
  - save_index(source_id, maps) → writes index JSON + updates manifest
"""

import json, re, time
from pathlib import Path

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    import sys
    sys.exit("pip install requests beautifulsoup4")

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "index"
CACHE_DIR = ROOT / ".cache"
SOURCES_FILE = ROOT / "sources.json"
MANIFEST_FILE = ROOT / "index" / "manifest.json"

USER_AGENT = "dnd-map-index/0.1 (personal project, https://github.com/dracoroboter/dnd-map-index)"

# ── Slugify ──────────────────────────────────────────────────────

def slugify(text):
    s = text.lower().strip()
    s = re.sub(r"[''']s\b", "s", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

# ── Tag guessing ─────────────────────────────────────────────────

KEYWORD_MAP = {
    "crypt": (["crypt", "undead"], "crypt"),
    "tomb": (["tomb", "undead"], "crypt"),
    "barrow": (["barrow", "undead"], "crypt"),
    "catacomb": (["catacombs", "undead"], "crypt"),
    "sepulch": (["tomb", "undead"], "crypt"),
    "ossuary": (["tomb", "undead"], "crypt"),
    "dungeon": (["dungeon"], "dungeon"),
    "cave": (["cave", "natural"], "cave"),
    "cavern": (["cavern", "natural"], "cave"),
    "grotto": (["grotto", "natural"], "cave"),
    "sewer": (["sewer", "urban"], "sewer"),
    "tavern": (["tavern", "social"], "tavern"),
    "inn": (["inn", "social"], "inn"),
    "alehouse": (["tavern", "social"], "tavern"),
    "temple": (["temple", "religious"], "temple"),
    "shrine": (["shrine", "religious"], "temple"),
    "church": (["church", "religious"], "temple"),
    "chapel": (["chapel", "religious"], "temple"),
    "basilica": (["basilica", "religious"], "temple"),
    "monastery": (["monastery", "religious"], "temple"),
    "tower": (["tower", "vertical"], "tower"),
    "spire": (["tower", "vertical"], "tower"),
    "castle": (["castle", "fortification"], "castle"),
    "keep": (["keep", "fortification"], "castle"),
    "fortress": (["fortress", "fortification"], "castle"),
    "fort": (["fort", "fortification"], "castle"),
    "citadel": (["citadel", "fortification"], "castle"),
    "bastion": (["bastion", "fortification"], "castle"),
    "manor": (["manor", "building"], "house"),
    "estate": (["estate", "building"], "house"),
    "house": (["house", "building"], "house"),
    "village": (["village", "settlement"], "village"),
    "town": (["town", "settlement"], "town"),
    "city": (["city", "settlement"], "city"),
    "island": (["island", "coastal"], "coast"),
    "isle": (["island", "coastal"], "coast"),
    "bridge": (["bridge"], "road"),
    "mine": (["mine"], "mine"),
    "pit": (["pit", "vertical"], "dungeon"),
    "vault": (["vault"], "dungeon"),
    "ruin": (["ruins"], "dungeon"),
    "pyramid": (["pyramid"], "temple"),
    "ship": (["ship", "naval"], "ship"),
    "dock": (["dock", "port"], "dock"),
    "harbour": (["harbour", "port"], "dock"),
    "harbor": (["harbor", "port"], "dock"),
    "market": (["market", "urban"], "market"),
    "shop": (["shop", "urban"], "shop"),
    "library": (["library"], "dungeon"),
    "lair": (["lair", "monster"], "cave"),
    "warren": (["warren"], "dungeon"),
    "labyrinth": (["labyrinth", "maze"], "dungeon"),
    "maze": (["maze"], "dungeon"),
    "lake": (["lake", "water"], "cave"),
    "river": (["river", "water"], "river"),
    "coast": (["coastal"], "coast"),
    "beach": (["beach", "coastal"], "coast"),
    "forest": (["forest", "natural"], "forest"),
    "wood": (["woods", "natural"], "forest"),
    "swamp": (["swamp", "natural"], "swamp"),
    "desert": (["desert"], "desert"),
    "mountain": (["mountain"], "mountain"),
    "camp": (["camp"], "camp"),
    "road": (["road"], "road"),
    "garden": (["garden"], "forest"),
    "prison": (["prison"], "dungeon"),
    "lab": (["laboratory"], "dungeon"),
    "theater": (["theater"], "house"),
    "arena": (["arena"], "dungeon"),
}

def guess_tags(title):
    t = title.lower()
    tags = set()
    env = ""
    for kw, (kt, ke) in KEYWORD_MAP.items():
        if re.search(r"\b" + re.escape(kw), t):
            tags.update(kt)
            if not env:
                env = ke
    if any(w in t for w in ["small", "little", "minor"]):
        tags.add("small")
    if any(w in t for w in ["great", "grand", "mega", "large"]):
        tags.add("large")
    return sorted(tags), env or "dungeon"

# ── Entry builder ────────────────────────────────────────────────

def get_source_config(source_id):
    if SOURCES_FILE.exists():
        sources = json.loads(SOURCES_FILE.read_text())
        for s in sources.get("sources", []):
            if s["id"] == source_id:
                return s
    return {}


def get_max_pages(source_id, default=30):
    """Get max_pages for a source from sources.json, or use default."""
    cfg = get_source_config(source_id)
    return cfg.get("max_pages", default)


def get_scan_interval(source_id, default=7):
    """Get scan_interval_days for a source from sources.json, or use default."""
    cfg = get_source_config(source_id)
    return cfg.get("scan_interval_days", default)

def make_entry(source_id, title, source_url, thumbnail_url="", image_url=""):
    """Create a map entry with defaults from sources.json. Tags left empty — use rescan or tag-assist."""
    cfg = get_source_config(source_id)
    return {
        "id": f"{source_id}-{slugify(title)}",
        "title": title,
        "author": cfg.get("name", source_id),
        "source_url": source_url,
        "image_url": image_url,
        "thumbnail_url": thumbnail_url,
        "license": cfg.get("license", {"type": "unknown", "attribution": ""}),
        "tags": [],
        "environment": "",
        "map_type": "battlemap",
        "style": cfg.get("style", ""),
        "format": cfg.get("format", ""),
        "status": "new",
        "date_indexed": time.strftime("%Y-%m-%d"),
    }

# ── Fetch with cache ─────────────────────────────────────────────

def fetch_cached(url, cache_name, force=False, max_age_days=None):
    CACHE_DIR.mkdir(exist_ok=True)
    cache_file = CACHE_DIR / cache_name
    if cache_file.exists() and not force:
        if max_age_days is not None:
            import os
            age_days = (time.time() - os.path.getmtime(cache_file)) / 86400
            if age_days > max_age_days:
                print(f"  Cache expired ({age_days:.0f}d > {max_age_days}d): {cache_file.name}")
            else:
                print(f"  Using cached {cache_file.name}")
                return cache_file.read_text(encoding="utf-8")
        else:
            print(f"  Using cached {cache_file.name}")
            return cache_file.read_text(encoding="utf-8")
    print(f"  Fetching {url[:80]}...")
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=30)
    r.raise_for_status()
    cache_file.write_text(r.text, encoding="utf-8")
    return r.text

# ── Save index + manifest ────────────────────────────────────────

def save_index(source_id, maps):
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    out = INDEX_DIR / f"{source_id}.json"
    # merge: preserve manually edited fields from existing index
    existing = {}
    if out.exists():
        existing = {m["id"]: m for m in json.loads(out.read_text(encoding="utf-8"))}
        for m in maps:
            old = existing.get(m["id"])
            if old:
                # preserve tags, environment, style if already set
                if old.get("tags"):
                    m["tags"] = old["tags"]
                if old.get("environment"):
                    m["environment"] = old["environment"]
                # preserve rescan fields
                for key in ("style_scanned", "last_checked", "status"):
                    if key in old and old[key]:
                        m[key] = old[key]

    # Delta report
    new_ids = {m["id"] for m in maps}
    old_ids = set(existing.keys())
    added = new_ids - old_ids
    removed = old_ids - new_ids
    kept = new_ids & old_ids
    print(f"  Delta: {len(added)} new, {len(kept)} existing, {len(removed)} removed")
    if added and len(added) <= 20:
        for mid in sorted(added):
            print(f"    + {mid}")
    if removed and len(removed) <= 20:
        for mid in sorted(removed):
            print(f"    - {mid}")

    out.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(maps)} maps → {out}")
    update_manifest()
    return {"source": source_id, "total": len(maps), "added": len(added), "kept": len(kept), "removed": len(removed)}


def update_manifest():
    """Rebuild manifest.json from all index files."""
    # Load existing manifest to preserve per-source last_scan dates
    old_manifest = {}
    if MANIFEST_FILE.exists():
        old_manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    old_scans = {e["source_id"]: e.get("last_scan") for e in old_manifest.get("files", [])}

    entries = []
    for f in sorted(INDEX_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        maps = json.loads(f.read_text(encoding="utf-8"))
        source_id = f.stem
        entries.append({
            "file": f.name,
            "source_id": source_id,
            "count": len(maps),
            "last_updated": time.strftime("%Y-%m-%d"),
            "last_scan": time.strftime("%Y-%m-%dT%H:%M:%S") if source_id not in old_scans or True else old_scans[source_id],
        })
    manifest = {
        "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "total_maps": sum(e["count"] for e in entries),
        "files": entries,
    }
    MANIFEST_FILE.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Manifest: {manifest['total_maps']} maps in {len(entries)} files")


SCAN_HISTORY_FILE = INDEX_DIR / "scan-history.json"
MAX_HISTORY = 10

def save_scan_history(entry):
    """Append a scan entry to scan-history.json, keeping last MAX_HISTORY entries."""
    history = []
    if SCAN_HISTORY_FILE.exists():
        try:
            history = json.loads(SCAN_HISTORY_FILE.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.insert(0, entry)
    history = history[:MAX_HISTORY]
    SCAN_HISTORY_FILE.write_text(json.dumps(history, indent=2, ensure_ascii=False), encoding="utf-8")
