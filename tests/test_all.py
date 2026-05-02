#!/usr/bin/env python3
"""Non-regression tests for dnd-map-index scripts.

Run after every update:
  python3 tests/test_all.py
"""

import json, sys, os, subprocess, tempfile, shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "index"
SCRIPTS = ROOT / "scripts"
SOURCES = ROOT / "sources.json"

passed = 0
failed = 0

def test(name, condition, detail=""):
    global passed, failed
    if condition:
        print(f"  ✅ {name}")
        passed += 1
    else:
        print(f"  ❌ {name}" + (f" — {detail}" if detail else ""))
        failed += 1

# ── 1. Structure tests ──────────────────────────────────────────

print("\n1. Structure")

test("sources.json exists", SOURCES.exists())
test("index/ directory exists", INDEX_DIR.exists())
test("at least one index file", len(list(INDEX_DIR.glob("*.json"))) > 0)
test("scripts/ directory exists", SCRIPTS.exists())

for script in ["grab-dyson.py", "search.py", "tag-assist.py", "rescan.py"]:
    test(f"scripts/{script} exists", (SCRIPTS / script).exists())

# ── 2. sources.json validation ───────────────────────────────────

print("\n2. sources.json")

sources = json.loads(SOURCES.read_text())
test("sources.json has 'sources' key", "sources" in sources)
test("at least 1 source defined", len(sources.get("sources", [])) > 0)

for s in sources.get("sources", []):
    sid = s.get("id", "?")
    test(f"source '{sid}' has required fields",
         all(k in s for k in ["id", "name", "status", "license", "thumbnail_policy", "download_policy", "indexing_method"]),
         f"missing: {[k for k in ['id','name','status','license','thumbnail_policy','download_policy','indexing_method'] if k not in s]}")
    test(f"source '{sid}' status is valid",
         s.get("status") in ("active", "planned", "backlog"),
         f"got: {s.get('status')}")

# ── 3. Index data validation ─────────────────────────────────────

print("\n3. Index data")

REQUIRED_FIELDS = ["id", "title", "author", "source_url", "license", "tags", "environment", "status", "date_indexed"]
VALID_STATUS = {"ok", "new", "broken", "removed"}
VALID_ENVS = {
    "dungeon", "cave", "crypt", "sewer", "mine",
    "tavern", "inn", "house", "castle", "temple", "tower", "shop",
    "forest", "mountain", "desert", "swamp", "coast", "river", "road", "camp",
    "city", "town", "village", "dock", "market",
    "ship", "underwater", "planar", "sky",
}

total_maps = 0
for f in sorted(INDEX_DIR.glob("*.json")):
    if f.name == "manifest.json":
        continue
    maps = json.loads(f.read_text())
    test(f"{f.name} is valid JSON array", isinstance(maps, list))
    test(f"{f.name} is not empty", len(maps) > 0)
    total_maps += len(maps)

    # check required fields on first and last entry
    for label, m in [("first", maps[0]), ("last", maps[-1])]:
        missing = [k for k in REQUIRED_FIELDS if k not in m]
        test(f"{f.name} {label} entry has required fields", not missing, f"missing: {missing}")

    # check all entries have valid status and environment
    bad_status = [m["id"] for m in maps if m.get("status") not in VALID_STATUS]
    test(f"{f.name} all status values valid", not bad_status,
         f"{len(bad_status)} invalid: {bad_status[:3]}")

    bad_env = [m["id"] for m in maps if m.get("environment") and m["environment"] not in VALID_ENVS]
    test(f"{f.name} all environment values valid", not bad_env,
         f"{len(bad_env)} invalid: {bad_env[:3]}")

    # check no duplicate IDs
    ids = [m["id"] for m in maps]
    dupes = [x for x in ids if ids.count(x) > 1]
    test(f"{f.name} no duplicate IDs", not dupes,
         f"{len(set(dupes))} duplicates: {list(set(dupes))[:3]}")

    # check all have license.type
    no_lic = [m["id"] for m in maps if not m.get("license", {}).get("type")]
    test(f"{f.name} all entries have license.type", not no_lic,
         f"{len(no_lic)} missing")

    # check tags is always a list
    bad_tags = [m["id"] for m in maps if not isinstance(m.get("tags"), list)]
    test(f"{f.name} tags is always a list", not bad_tags,
         f"{len(bad_tags)} not list")

test(f"total maps in index: {total_maps}", total_maps > 0)

# manifest validation
manifest_file = INDEX_DIR / "manifest.json"
test("manifest.json exists", manifest_file.exists())
if manifest_file.exists():
    manifest = json.loads(manifest_file.read_text())
    test("manifest has 'files' key", "files" in manifest)
    test("manifest has 'total_maps' key", "total_maps" in manifest)
    test("manifest total_maps matches actual", manifest.get("total_maps") == total_maps,
         f"manifest={manifest.get('total_maps')}, actual={total_maps}")
    test("manifest files count matches index files",
         len(manifest.get("files", [])) == len(list(f for f in INDEX_DIR.glob("*.json") if f.name != "manifest.json")))

# ── 4. search.py smoke test ──────────────────────────────────────

print("\n4. search.py")

result = subprocess.run(
    [sys.executable, str(SCRIPTS / "search.py"), "--stats"],
    capture_output=True, text=True, cwd=str(ROOT)
)
test("search.py --stats runs", result.returncode == 0, result.stderr[:100] if result.stderr else "")
test("search.py --stats shows total", "Total maps:" in result.stdout, result.stdout[:100])

result = subprocess.run(
    [sys.executable, str(SCRIPTS / "search.py"), "--text", "crypt", "-n", "3"],
    capture_output=True, text=True, cwd=str(ROOT)
)
test("search.py --text crypt returns results", "maps found" in result.stdout.lower() or "crypt" in result.stdout.lower())

result = subprocess.run(
    [sys.executable, str(SCRIPTS / "search.py"), "--env", "tavern"],
    capture_output=True, text=True, cwd=str(ROOT)
)
test("search.py --env tavern runs", result.returncode == 0)

# ── 5. rescan.py smoke test ──────────────────────────────────────

print("\n5. rescan.py")

result = subprocess.run(
    [sys.executable, str(SCRIPTS / "rescan.py"), "--stats"],
    capture_output=True, text=True, cwd=str(ROOT)
)
test("rescan.py --stats runs", result.returncode == 0, result.stderr[:100] if result.stderr else "")
test("rescan.py --stats shows source", "dyson-logos" in result.stdout)

# ── 6. webapp validation ─────────────────────────────────────────

print("\n6. Webapp")

index_html = ROOT / "index.html"
test("index.html exists", index_html.exists())

if index_html.exists():
    html = index_html.read_text()
    test("index.html references index/ JSON", "index/" in html)
    test("index.html has search function", "function search" in html or "function onFilter" in html)
    test("index.html has pagination", "PAGE_SIZE" in html)
    test("index.html has lazy loading", 'loading="lazy"' in html or "loading='lazy'" in html)
    test("index.html has about section", "about" in html.lower())
    test("index.html has copyright contact", "dracoroboter" in html)

# ── Summary ───────────────────────────────────────────────────────

print(f"\n{'='*50}")
print(f"  Results: {passed} passed, {failed} failed")
print(f"{'='*50}")
sys.exit(1 if failed else 0)
