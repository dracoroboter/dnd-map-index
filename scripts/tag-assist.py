#!/usr/bin/env python3
"""Interactive tagger: shows maps one by one, suggests tags from title, user confirms/edits.

Usage:
  python tag-assist.py                    # tag all untagged maps
  python tag-assist.py --pick 20          # pick 20 diverse maps to tag
  python tag-assist.py --pick 20 --diverse # pick 20 maximally diverse by guessed environment
"""

import json, re, sys, random
from pathlib import Path

INDEX = Path(__file__).resolve().parent.parent / "index" / "dyson-logos.json"

ENVIRONMENTS = [
    "dungeon", "cave", "crypt", "sewer", "mine",
    "tavern", "inn", "house", "castle", "temple", "tower", "shop",
    "forest", "mountain", "desert", "swamp", "coast", "river", "road", "camp",
    "city", "town", "village", "dock", "market",
    "ship", "underwater", "planar", "sky",
]

# title keywords → suggested tags + environment
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
    "hall": (["hall"], "dungeon"),
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
}

def guess_tags(title):
    """Guess tags and environment from title keywords."""
    title_lower = title.lower()
    tags = set()
    env = ""
    for keyword, (ktags, kenv) in KEYWORD_MAP.items():
        if keyword in title_lower:
            tags.update(ktags)
            if not env:
                env = kenv
    # size hints
    if any(w in title_lower for w in ["small", "little", "minor"]):
        tags.add("small")
    if any(w in title_lower for w in ["great", "grand", "mega", "large"]):
        tags.add("large")
    return sorted(tags), env or "dungeon"

def pick_diverse(maps, n):
    """Pick n maps spread across different guessed environments."""
    by_env = {}
    for m in maps:
        _, env = guess_tags(m["title"])
        by_env.setdefault(env, []).append(m)
    picked = []
    envs = list(by_env.keys())
    random.shuffle(envs)
    i = 0
    while len(picked) < n and any(by_env.values()):
        env = envs[i % len(envs)]
        if by_env.get(env):
            picked.append(by_env[env].pop(0))
        i += 1
        if i > n * 10:
            break
    return picked[:n]

def tag_interactive(maps):
    """Interactive tagging loop."""
    changed = 0
    total = len(maps)
    print(f"\n{'='*60}")
    print(f"  Tag Assist — {total} maps to tag")
    print(f"  Commands: ENTER=accept, e=edit tags, v=edit env, s=skip, q=quit")
    print(f"{'='*60}\n")

    for i, m in enumerate(maps):
        suggested_tags, suggested_env = guess_tags(m["title"])
        print(f"[{i+1}/{total}] {m['title']}")
        print(f"  URL: {m['source_url']}")
        print(f"  Suggested env:  {suggested_env}")
        print(f"  Suggested tags: {', '.join(suggested_tags) or '(none)'}")
        while True:
            choice = input("  > ").strip().lower()
            if choice == "" or choice == "y":
                m["tags"] = suggested_tags
                m["environment"] = suggested_env
                m["status"] = "ok"
                changed += 1
                break
            elif choice == "e":
                raw = input("  tags (comma-sep): ").strip()
                m["tags"] = [t.strip() for t in raw.split(",") if t.strip()]
                m["environment"] = suggested_env
                m["status"] = "ok"
                changed += 1
                break
            elif choice == "v":
                new_env = input(f"  env [{suggested_env}]: ").strip() or suggested_env
                m["environment"] = new_env
                m["tags"] = suggested_tags
                m["status"] = "ok"
                changed += 1
                break
            elif choice == "s":
                break
            elif choice == "q":
                return changed
            else:
                print("  ENTER=accept, e=edit tags, v=edit env, s=skip, q=quit")
        print()
    return changed

def main():
    if not INDEX.exists():
        sys.exit(f"Run grab-dyson.py first. Missing: {INDEX}")
    maps = json.loads(INDEX.read_text(encoding="utf-8"))

    pick = 0
    diverse = False
    for arg in sys.argv[1:]:
        if arg == "--diverse":
            diverse = True
        elif arg.startswith("--pick"):
            pass
        else:
            try:
                pick = int(arg)
            except ValueError:
                pass
    if "--pick" in sys.argv:
        idx = sys.argv.index("--pick")
        if idx + 1 < len(sys.argv):
            pick = int(sys.argv[idx + 1])

    if pick > 0:
        untagged = [m for m in maps if not m.get("tags")]
        if diverse:
            subset = pick_diverse(untagged, pick)
        else:
            subset = untagged[:pick]
        print(f"Selected {len(subset)} maps to tag")
        changed = tag_interactive(subset)
        # merge back
        tagged_ids = {m["id"]: m for m in subset}
        for i, m in enumerate(maps):
            if m["id"] in tagged_ids:
                maps[i] = tagged_ids[m["id"]]
    else:
        untagged = [m for m in maps if not m.get("tags")]
        if not untagged:
            print("All maps already tagged!")
            return
        changed = tag_interactive(untagged)
        tagged_ids = {m["id"]: m for m in untagged}
        for i, m in enumerate(maps):
            if m["id"] in tagged_ids:
                maps[i] = tagged_ids[m["id"]]

    INDEX.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {changed} tagged maps → {INDEX}")

if __name__ == "__main__":
    main()
