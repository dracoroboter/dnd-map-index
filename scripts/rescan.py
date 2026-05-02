#!/usr/bin/env python3
"""Rescan index: check URLs, detect B&W vs color from thumbnails.

Usage:
  python rescan.py                    # check 5 unscanned maps for color
  python rescan.py --color 20         # check 20
  python rescan.py --check-urls 10    # verify 10 oldest-checked URLs
  python rescan.py --stats            # show scan progress
"""

import json, sys, time, argparse, random
from pathlib import Path

try:
    import requests
    from PIL import Image
    from io import BytesIO
except ImportError:
    sys.exit("pip install requests beautifulsoup4 Pillow")

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grab_core import guess_tags

INDEX_DIR = Path(__file__).resolve().parent.parent / "index"
STATUS_FILE = Path(__file__).resolve().parent.parent / "rescan-status.json"

def load_all():
    """Load all index files, return (maps, path) pairs."""
    result = []
    for f in sorted(INDEX_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        maps = json.loads(f.read_text(encoding="utf-8"))
        result.append((maps, f))
    return result

def detect_color(url):
    """Download thumbnail and return 'color' or 'bw-ink'."""
    r = requests.get(url, timeout=15, headers={"User-Agent": "dnd-map-index/0.1"})
    r.raise_for_status()
    img = Image.open(BytesIO(r.content)).convert("RGB")
    pixels = list(img.getdata())
    sat = sum(max(p) - min(p) for p in pixels) / len(pixels)
    return "color" if sat > 15 else "bw-ink"

def save_status(operation, maps_list, details=None):
    """Save machine-readable status after each run."""
    status = {
        "last_run": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "operation": operation,
        "sources": {}
    }
    for maps, path in maps_list:
        total = len(maps)
        status["sources"][path.stem] = {
            "total": total,
            "color_scanned": sum(1 for m in maps if m.get("style_scanned")),
            "color_bw": sum(1 for m in maps if m.get("style") == "bw-ink" and m.get("style_scanned")),
            "color_color": sum(1 for m in maps if m.get("style") == "color" and m.get("style_scanned")),
            "url_checked": sum(1 for m in maps if m.get("last_checked")),
            "url_broken": sum(1 for m in maps if m.get("status") == "broken"),
            "tagged": sum(1 for m in maps if m.get("tags")),
            "with_thumbnail": sum(1 for m in maps if m.get("thumbnail_url")),
        }
    if details:
        status["details"] = details
    STATUS_FILE.write_text(json.dumps(status, indent=2, ensure_ascii=False), encoding="utf-8")

def cmd_color(maps_list, n):
    """Detect B&W vs color for n maps that haven't been scanned yet."""
    for maps, path in maps_list:
        # pick maps without style_scanned flag, shuffle for variety
        unscanned = [m for m in maps if not m.get("style_scanned")]
        random.shuffle(unscanned)
        batch = unscanned[:n]
        if not batch:
            print(f"  {path.stem}: all scanned")
            continue
        print(f"  {path.stem}: scanning {len(batch)} of {len(unscanned)} remaining")
        changed = 0
        for m in batch:
            if not m.get("thumbnail_url"):
                m["style_scanned"] = True
                continue
            try:
                style = detect_color(m["thumbnail_url"])
                m["style"] = style
                m["style_scanned"] = True
                changed += 1
                label = "COLOR" if style == "color" else "B&W  "
                print(f"    {label} {m['title'][:50]}")
                time.sleep(0.2)
            except Exception as e:
                print(f"    ERROR {m['title'][:40]}: {e}")
        path.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"    saved {changed} updates")
    save_status("color", maps_list, {"scanned": n})

def cmd_check_urls(maps_list, n):
    """HEAD-check n oldest-checked URLs."""
    for maps, path in maps_list:
        candidates = sorted(maps, key=lambda m: m.get("last_checked", ""))
        batch = candidates[:n]
        print(f"  {path.stem}: checking {len(batch)} URLs")
        changed = 0
        for m in batch:
            try:
                r = requests.head(m["source_url"], timeout=10, allow_redirects=True,
                                  headers={"User-Agent": "dnd-map-index/0.1"})
                if r.status_code < 400:
                    m["status"] = "ok"
                else:
                    m["status"] = "broken"
                    print(f"    BROKEN [{r.status_code}] {m['title'][:50]}")
            except Exception as e:
                m["status"] = "broken"
                print(f"    BROKEN {m['title'][:40]}: {e}")
            m["last_checked"] = time.strftime("%Y-%m-%d")
            changed += 1
            time.sleep(0.2)
        path.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"    checked {changed}")
    save_status("check-urls", maps_list, {"checked": n})

def cmd_stats(maps_list):
    for maps, path in maps_list:
        total = len(maps)
        scanned = sum(1 for m in maps if m.get("style_scanned"))
        bw = sum(1 for m in maps if m.get("style") == "bw-ink" and m.get("style_scanned"))
        color = sum(1 for m in maps if m.get("style") == "color" and m.get("style_scanned"))
        checked = sum(1 for m in maps if m.get("last_checked"))
        broken = sum(1 for m in maps if m.get("status") == "broken")
        tagged = sum(1 for m in maps if m.get("tags"))
        untagged = total - tagged
        print(f"{path.stem}: {total} maps, tagged {tagged}/{total} (untagged={untagged}), color-scanned {scanned}/{total} (B&W={bw}, color={color}), URL-checked {checked}/{total}, broken={broken}")

def cmd_autotag(maps_list):
    """Auto-tag all maps that have no tags, using guess_tags from title."""
    for maps, path in maps_list:
        untagged = [m for m in maps if not m.get("tags")]
        if not untagged:
            print(f"  {path.stem}: all tagged")
            continue
        changed = 0
        for m in untagged:
            tags, env = guess_tags(m["title"])
            m["tags"] = tags if tags else [env]
            m["environment"] = env
            if m.get("status") == "new":
                m["status"] = "ok"
            changed += 1
        path.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"  {path.stem}: auto-tagged {changed} maps")
    save_status("autotag", maps_list)

def main():
    p = argparse.ArgumentParser(description="Rescan dnd-map-index")
    p.add_argument("--color", type=int, nargs="?", const=5, help="Detect B&W vs color (default 5)")
    p.add_argument("--check-urls", type=int, nargs="?", const=10, help="HEAD-check URLs (default 10)")
    p.add_argument("--autotag", action="store_true", help="Auto-tag untagged maps from title")
    p.add_argument("--stats", action="store_true")
    args = p.parse_args()

    maps_list = load_all()

    if args.stats:
        cmd_stats(maps_list)
    elif args.autotag:
        cmd_autotag(maps_list)
    elif args.check_urls is not None:
        cmd_check_urls(maps_list, args.check_urls)
    elif args.color is not None:
        cmd_color(maps_list, args.color)
    else:
        # default: scan 5 for color
        cmd_color(maps_list, 5)

if __name__ == "__main__":
    main()
