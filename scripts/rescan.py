#!/usr/bin/env python3
"""Rescan index: unified maintenance for all maps.

Default (no flags): process N maps doing ALL pending checks:
  - URL existence (always)
  - Auto-tag (only if tags empty)
  - Color detection (only if not yet scanned)

Usage:
  python rescan.py              # process 5 maps (all checks)
  python rescan.py 20           # process 20 maps
  python rescan.py --autotag    # force re-tag ALL maps (overwrites existing)
  python rescan.py --color 10   # only color-detect 10 maps
  python rescan.py --check-urls 10  # only URL-check 10 maps
  python rescan.py --stats      # show progress
"""

import json, sys, time, argparse, random
from pathlib import Path

try:
    import requests
    from PIL import Image
    from io import BytesIO
except ImportError:
    sys.exit("pip install requests Pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grab_core import guess_tags

INDEX_DIR = Path(__file__).resolve().parent.parent / "index"
STATUS_FILE = Path(__file__).resolve().parent.parent / "rescan-status.json"
UA = {"User-Agent": "dnd-map-index/0.1"}

def load_all():
    result = []
    for f in sorted(INDEX_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        result.append((json.loads(f.read_text(encoding="utf-8")), f))
    return result

def save_file(maps, path):
    path.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")

def detect_color(url):
    r = requests.get(url, timeout=15, headers=UA)
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    pixels = list(img.getdata())
    sat = sum(max(p) - min(p) for p in pixels) / len(pixels)
    return "color" if sat > 15 else "bw-ink"

def check_url(url):
    r = requests.head(url, timeout=10, allow_redirects=True, headers=UA)
    return r.status_code < 400

def save_status(operation, maps_list, details=None):
    status = {"last_run": time.strftime("%Y-%m-%dT%H:%M:%S"), "operation": operation, "sources": {}}
    for maps, path in maps_list:
        status["sources"][path.stem] = {
            "total": len(maps),
            "tagged": sum(1 for m in maps if m.get("tags")),
            "color_scanned": sum(1 for m in maps if m.get("style_scanned")),
            "url_checked": sum(1 for m in maps if m.get("last_checked")),
            "url_broken": sum(1 for m in maps if m.get("status") == "broken"),
            "with_thumbnail": sum(1 for m in maps if m.get("thumbnail_url")),
        }
    if details:
        status["details"] = details
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

# ── Unified rescan ───────────────────────────────────────────────

def needs_work(m):
    """True if this map has any pending check."""
    if not m.get("tags"):
        return True
    if not m.get("style_scanned") and m.get("thumbnail_url"):
        return True
    return True  # URL check is always useful

def cmd_rescan(maps_list, n):
    """Process n maps: URL check (always), autotag (if needed), color (if needed)."""
    for maps, path in maps_list:
        # shuffle for variety across runs
        candidates = list(maps)
        random.shuffle(candidates)
        batch = candidates[:n]
        print(f"  {path.stem}: processing {len(batch)} maps")
        tags_done = color_done = url_done = broken = 0
        for m in batch:
            # 1. Auto-tag if empty
            if not m.get("tags"):
                tags, env = guess_tags(m["title"])
                m["tags"] = tags if tags else [env]
                m["environment"] = env
                if m.get("status") == "new":
                    m["status"] = "ok"
                tags_done += 1
            # 2. Color detect if not scanned
            if not m.get("style_scanned") and m.get("thumbnail_url"):
                try:
                    m["style"] = detect_color(m["thumbnail_url"])
                    m["style_scanned"] = True
                    color_done += 1
                except Exception:
                    pass  # skip silently, will retry next run
            # 3. URL check (always)
            try:
                if check_url(m["source_url"]):
                    m["status"] = "ok"
                else:
                    m["status"] = "broken"
                    broken += 1
                    print(f"    BROKEN {m['title'][:50]}")
            except Exception:
                m["status"] = "broken"
                broken += 1
            m["last_checked"] = time.strftime("%Y-%m-%d")
            url_done += 1
            time.sleep(0.3)
        save_file(maps, path)
        print(f"    tagged={tags_done} color={color_done} url={url_done} broken={broken}")
    save_status("rescan", maps_list, {"processed": n})

# ── Single-purpose commands (shortcuts) ──────────────────────────

def cmd_autotag(maps_list):
    """Force auto-tag on ALL maps, overwriting existing tags."""
    for maps, path in maps_list:
        for m in maps:
            tags, env = guess_tags(m["title"])
            m["tags"] = tags if tags else [env]
            m["environment"] = env
            if m.get("status") == "new":
                m["status"] = "ok"
        save_file(maps, path)
        print(f"  {path.stem}: force-tagged {len(maps)} maps")
    save_status("autotag", maps_list)

def cmd_color(maps_list, n):
    """Force color detection on n maps, even if already scanned."""
    for maps, path in maps_list:
        candidates = [m for m in maps if m.get("thumbnail_url")]
        random.shuffle(candidates)
        batch = candidates[:n]
        if not batch:
            print(f"  {path.stem}: no maps with thumbnails")
            continue
        print(f"  {path.stem}: force-scanning {len(batch)} maps")
        for m in batch:
            try:
                m["style"] = detect_color(m["thumbnail_url"])
                m["style_scanned"] = True
                print(f"    {'COLOR' if m['style']=='color' else 'B&W  '} {m['title'][:50]}")
                time.sleep(0.2)
            except Exception as e:
                print(f"    ERROR {m['title'][:40]}: {e}")
        save_file(maps, path)
    save_status("color", maps_list, {"scanned": n})

def cmd_check_urls(maps_list, n):
    """Force URL check on n maps, even if recently checked."""
    for maps, path in maps_list:
        candidates = list(maps)
        random.shuffle(candidates)
        batch = candidates[:n]
        print(f"  {path.stem}: checking {len(batch)} URLs")
        for m in batch:
            try:
                ok = check_url(m["source_url"])
                m["status"] = "ok" if ok else "broken"
                if not ok:
                    print(f"    BROKEN {m['title'][:50]}")
            except Exception as e:
                m["status"] = "broken"
                print(f"    BROKEN {m['title'][:40]}: {e}")
            m["last_checked"] = time.strftime("%Y-%m-%d")
            time.sleep(0.2)
        save_file(maps, path)
    save_status("check-urls", maps_list, {"checked": n})

def cmd_stats(maps_list):
    for maps, path in maps_list:
        t = len(maps)
        tagged = sum(1 for m in maps if m.get("tags"))
        scanned = sum(1 for m in maps if m.get("style_scanned"))
        checked = sum(1 for m in maps if m.get("last_checked"))
        broken = sum(1 for m in maps if m.get("status") == "broken")
        print(f"{path.stem}: {t} maps | tagged {tagged}/{t} | color {scanned}/{t} | url-checked {checked}/{t} | broken {broken}")

# ── Main ─────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Rescan dnd-map-index")
    p.add_argument("n", type=int, nargs="?", default=5, help="Maps to process (default 5)")
    p.add_argument("--autotag", action="store_true", help="Only: auto-tag untagged maps")
    p.add_argument("--color", type=int, nargs="?", const=5, help="Only: detect B&W vs color")
    p.add_argument("--check-urls", type=int, nargs="?", const=10, help="Only: HEAD-check URLs")
    p.add_argument("--stats", action="store_true", help="Show progress")
    args = p.parse_args()

    maps_list = load_all()

    if args.stats:
        cmd_stats(maps_list)
    elif args.autotag:
        cmd_autotag(maps_list)
    elif args.color is not None:
        cmd_color(maps_list, args.color)
    elif args.check_urls is not None:
        cmd_check_urls(maps_list, args.check_urls)
    else:
        cmd_rescan(maps_list, args.n)

if __name__ == "__main__":
    main()
