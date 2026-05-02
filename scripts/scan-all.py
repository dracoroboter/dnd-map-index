#!/usr/bin/env python3
"""Unified scan: re-grab sources + URL check existing maps.

Budget-based: allocates fetches across sources by priority.
Sources with expired cache (older than scan_interval_days) go first.
50% budget for grabbing new maps, 50% for URL-checking existing ones.

Usage:
  python3 scripts/scan-all.py              # default budget: 100 fetches
  python3 scripts/scan-all.py --budget 50  # custom budget
  python3 scripts/scan-all.py --source reddit  # only one source
  python3 scripts/scan-all.py --dry-run    # show plan without executing
"""

import argparse, json, os, random, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import (INDEX_DIR, CACHE_DIR, SOURCES_FILE, MANIFEST_FILE,
                        get_source_config, get_scan_interval, get_max_pages)

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_BUDGET = 100

# ── Source priority ──────────────────────────────────────────────

def get_source_staleness(source_id):
    """Return how many days since last scan. Higher = more stale."""
    if not MANIFEST_FILE.exists():
        return 999
    manifest = json.loads(MANIFEST_FILE.read_text(encoding="utf-8"))
    for f in manifest.get("files", []):
        if f["source_id"] == source_id:
            last = f.get("last_scan", "")
            if last:
                from datetime import datetime
                try:
                    dt = datetime.fromisoformat(last)
                    return (datetime.now() - dt).total_seconds() / 86400
                except Exception:
                    pass
    return 999  # never scanned


def get_sources_by_priority(only_source=None):
    """Return sources sorted by urgency (most stale first, weighted by interval)."""
    sources = json.loads(SOURCES_FILE.read_text(encoding="utf-8"))
    result = []
    for s in sources.get("sources", []):
        if s.get("status") not in ("active", "experimental"):
            continue
        if only_source and s["id"] != only_source:
            continue
        interval = s.get("scan_interval_days", 7)
        staleness = get_source_staleness(s["id"])
        overdue = staleness / interval  # >1 means cache expired
        result.append({
            "id": s["id"],
            "name": s["name"],
            "interval": interval,
            "staleness_days": round(staleness, 1),
            "overdue_ratio": round(overdue, 2),
            "max_pages": s.get("max_pages", 30),
        })
    result.sort(key=lambda x: -x["overdue_ratio"])
    return result


# ── Grab phase ───────────────────────────────────────────────────

GRABBER_MAP = {
    "dyson-logos": "grab-dyson.py",
    "2minute-tabletop": "grab-2minute.py",
    "tom-cartos": "grab-tomcartos.py",
    "seafoot-games": "grab-seafoot.py",
    "dice-grimorium": "grab-dicegrimorium.py",
    "reddit-curated": "grab-reddit.py",
    "forgotten-adventures": "grab-forgottenadv.py",
}


def estimate_pages(source_id):
    """Estimate how many fetches a grabber will do (from cache file count)."""
    prefix_map = {
        "dyson-logos": "dyson-",
        "2minute-tabletop": "2minute-",
        "tom-cartos": "tomcartos-",
        "seafoot-games": "seafoot-",
        "dice-grimorium": "dicegrimorium-",
        "reddit-curated": "reddit-",
        "forgotten-adventures": "forgottenadv-",
    }
    prefix = prefix_map.get(source_id, source_id)
    if not CACHE_DIR.exists():
        return 5
    expired = 0
    interval = get_scan_interval(source_id, 7)
    for f in CACHE_DIR.iterdir():
        if f.name.startswith(prefix):
            age = (time.time() - f.stat().st_mtime) / 86400
            if age > interval:
                expired += 1
    return max(expired, 1)


def run_grabber(source_id):
    """Run a grabber and return its output."""
    script = GRABBER_MAP.get(source_id)
    if not script:
        return f"  No grabber for {source_id}", {}
    script_path = ROOT / "scripts" / script
    import subprocess
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True, text=True, cwd=str(ROOT)
    )
    output = result.stdout + result.stderr
    # Parse delta from output
    delta = {"source": source_id, "added": 0, "kept": 0, "removed": 0, "total": 0}
    for line in output.split("\n"):
        if "Delta:" in line:
            import re
            m = re.search(r"(\d+) new, (\d+) existing, (\d+) removed", line)
            if m:
                delta["added"] = int(m.group(1))
                delta["kept"] = int(m.group(2))
                delta["removed"] = int(m.group(3))
                delta["total"] = delta["added"] + delta["kept"]
    return output, delta


# ── URL check phase ──────────────────────────────────────────────

def url_check_batch(budget):
    """Check URLs of random existing maps."""
    import requests
    UA = {"User-Agent": "dnd-map-index/0.2"}
    checked = broken = 0
    all_maps_files = []
    for f in sorted(INDEX_DIR.glob("*.json")):
        if f.name == "manifest.json":
            continue
        maps = json.loads(f.read_text(encoding="utf-8"))
        all_maps_files.append((maps, f))

    # Pick random maps across all sources
    all_maps = [(m, f) for maps, f in all_maps_files for m in maps]
    random.shuffle(all_maps)
    batch = all_maps[:budget]

    modified_files = set()
    for m, f in batch:
        try:
            r = requests.head(m["source_url"], timeout=10, allow_redirects=True, headers=UA)
            was_broken = m.get("status") == "broken"
            if r.status_code < 400:
                m["status"] = "ok"
            else:
                m["status"] = "broken"
                broken += 1
                print(f"    BROKEN {m['title'][:50]}")
        except Exception:
            m["status"] = "broken"
            broken += 1
        m["last_checked"] = time.strftime("%Y-%m-%d")
        checked += 1
        modified_files.add(f)
        time.sleep(0.2)

    # Save modified files
    for f in modified_files:
        maps = json.loads(f.read_text(encoding="utf-8"))
        # Apply changes (maps are references, already modified)
        f.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")

    return checked, broken


# ── Main ─────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Unified scan for dnd-map-index")
    p.add_argument("--budget", type=int, default=DEFAULT_BUDGET, help="Max total fetches (default 100)")
    p.add_argument("--source", type=str, help="Only scan this source")
    p.add_argument("--dry-run", action="store_true", help="Show plan without executing")
    args = p.parse_args()

    sources = get_sources_by_priority(args.source)
    if not sources:
        print("No sources to scan.")
        return

    grab_budget = args.budget // 2
    check_budget = args.budget - grab_budget

    print(f"=== scan-all (budget: {args.budget} fetches) ===")
    print(f"  Grab budget: {grab_budget} | URL check budget: {check_budget}")
    print()

    # Show plan
    print("Source priority:")
    for s in sources:
        expired = "⚠️  EXPIRED" if s["overdue_ratio"] >= 1 else "✅ fresh"
        print(f"  {s['name']:30s} stale {s['staleness_days']:5.1f}d / interval {s['interval']}d  {expired}")
    print()

    if args.dry_run:
        return

    # Phase 1: Grab (50% budget)
    print("── Phase 1: Grab new maps ──")
    remaining = grab_budget
    source_deltas = []
    for s in sources:
        if remaining <= 0:
            break
        est = estimate_pages(s["id"])
        if est > remaining:
            print(f"  {s['name']}: skipping (needs ~{est} fetches, {remaining} left)")
            continue
        print(f"\n  {s['name']} (~{est} fetches):")
        output, delta = run_grabber(s["id"])
        for line in output.strip().split("\n"):
            print(f"    {line}")
        source_deltas.append(delta)
        remaining -= est

    # Phase 2: URL check (50% budget)
    print(f"\n── Phase 2: URL check ({check_budget} maps) ──")
    checked, broken = url_check_batch(check_budget)
    print(f"  Checked {checked} URLs, {broken} broken")

    # Save scan history
    from grab_core import save_scan_history
    history_entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "budget": args.budget,
        "sources_scanned": len(source_deltas),
        "url_checked": checked,
        "url_broken": broken,
        "deltas": source_deltas,
        "totals": {
            "added": sum(d["added"] for d in source_deltas),
            "kept": sum(d["kept"] for d in source_deltas),
            "removed": sum(d["removed"] for d in source_deltas),
        }
    }
    save_scan_history(history_entry)
    print(f"\n  Scan history saved ({len(source_deltas)} sources, +{history_entry['totals']['added']} new, -{history_entry['totals']['removed']} removed)")

    print(f"\n=== Done ===")


if __name__ == "__main__":
    main()
