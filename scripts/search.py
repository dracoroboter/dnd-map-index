#!/usr/bin/env python3
"""Search the map index. Examples:
  python search.py --env crypt
  python search.py --env tavern --license free
  python search.py --text "goblin"
  python search.py --tag ruins
  python search.py --tagged-only
"""

import json, sys, argparse
from pathlib import Path

INDEX_DIR = Path(__file__).resolve().parent.parent / "index"

def load_all():
    maps = []
    for f in sorted(INDEX_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        maps.extend(json.loads(f.read_text(encoding="utf-8")))
    return maps

def main():
    p = argparse.ArgumentParser(description="Search dnd-map-index")
    p.add_argument("--env", help="Filter by environment")
    p.add_argument("--tag", help="Filter by tag")
    p.add_argument("--text", help="Search in title")
    p.add_argument("--license", choices=["free", "unknown"], help="Filter by license category")
    p.add_argument("--author", help="Filter by author")
    p.add_argument("--tagged-only", action="store_true", help="Show only tagged maps")
    p.add_argument("--stats", action="store_true", help="Show index statistics")
    p.add_argument("-n", type=int, default=20, help="Max results (default 20)")
    args = p.parse_args()

    maps = load_all()

    if args.stats:
        tagged = sum(1 for m in maps if m.get("tags"))
        ok = sum(1 for m in maps if m.get("status") == "ok")
        from collections import Counter
        envs = Counter(m.get("environment", "?") for m in maps if m.get("environment"))
        print(f"Total maps: {len(maps)}")
        print(f"Tagged:     {tagged}")
        print(f"Status ok:  {ok}")
        print(f"\nEnvironments (tagged only):")
        for env, count in envs.most_common():
            print(f"  {env:12s} {count}")
        return

    # filter out removed
    maps = [m for m in maps if m.get("status") != "removed"]

    if args.tagged_only:
        maps = [m for m in maps if m.get("tags")]
    if args.env:
        maps = [m for m in maps if m.get("environment") == args.env]
    if args.tag:
        maps = [m for m in maps if args.tag in m.get("tags", [])]
    if args.text:
        q = args.text.lower()
        maps = [m for m in maps if q in m.get("title", "").lower()]
    if args.license == "free":
        maps = [m for m in maps if m.get("license", {}).get("type") != "unknown"]
    elif args.license == "unknown":
        maps = [m for m in maps if m.get("license", {}).get("type") == "unknown"]
    if args.author:
        q = args.author.lower()
        maps = [m for m in maps if q in m.get("author", "").lower()]

    if not maps:
        print("No maps found.")
        return

    print(f"Found {len(maps)} maps" + (f" (showing first {args.n})" if len(maps) > args.n else ""))
    print()
    for m in maps[:args.n]:
        env = m.get("environment", "?")
        tags = ", ".join(m.get("tags", [])) or "-"
        lic = m.get("license", {}).get("type", "?")
        status = m.get("status", "?")
        print(f"  {m['title']}")
        print(f"    env={env}  tags=[{tags}]  license={lic}  status={status}")
        print(f"    {m['source_url']}")
        print()

if __name__ == "__main__":
    main()
