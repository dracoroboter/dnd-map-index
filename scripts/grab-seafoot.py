#!/usr/bin/env python3
"""Grab plugin: Seafoot Games free battlemaps.

Scrapes paginated WordPress blog listing → index/seafoot-games.json
Only indexes free maps from the public blog. Does NOT download images.
"""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index, get_max_pages, get_scan_interval
from bs4 import BeautifulSoup

SOURCE_ID = "seafoot-games"
BASE_URL = "https://www.seafootgames.com/the-best-free-dnd-battlemaps-realistic-grimdark-fantasy/"

# Map Seafoot category names to our environment/tags
CAT_MAP = {
    "battlefield": (["battlefield"], "dungeon"),
    "camp": (["camp"], "camp"),
    "castle": (["castle", "fortification"], "castle"),
    "manor": (["manor", "building"], "house"),
    "keep": (["keep", "fortification"], "castle"),
    "cavern": (["cavern", "natural"], "cave"),
    "coastal": (["coastal"], "coast"),
    "demonic": (["demonic"], "dungeon"),
    "desert": (["desert"], "desert"),
    "dungeon": (["dungeon"], "dungeon"),
    "dwarven": (["dwarven"], "dungeon"),
    "elven": (["elven"], "forest"),
    "forest": (["forest", "natural"], "forest"),
    "horror": (["horror"], "dungeon"),
    "magical": (["magical"], "dungeon"),
    "mountain": (["mountain"], "mountain"),
    "multi-level": (["multi-level"], ""),
    "road": (["road"], "road"),
    "sci-fi": (["sci-fi"], "dungeon"),
    "ship": (["ship", "naval"], "ship"),
    "swamp": (["swamp", "natural"], "swamp"),
    "temple": (["temple", "religious"], "temple"),
    "town": (["town", "settlement"], "town"),
    "city": (["city", "settlement"], "city"),
    "underworld": (["underworld"], "dungeon"),
    "volcanic": (["volcanic"], "dungeon"),
    "winter": (["winter"], "mountain"),
}


def parse_categories(article):
    """Extract tags and environment from article categories."""
    tags = set()
    env = ""
    for a in article.select(".entry-categories a, .cat-links a, a[rel=category]"):
        cat = a.get_text(strip=True).lower()
        for key, (ktags, kenv) in CAT_MAP.items():
            if key in cat:
                tags.update(ktags)
                if not env and kenv:
                    env = kenv
    return sorted(tags), env


def clean_title(title):
    """Remove common suffixes like 'Free 60x40 DnD Battlemap'."""
    title = re.sub(r"\s+Free\s+\d+[×x]\d+\s+(Multi-Level\s+)?DnD\s+Battlemap\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+Free\s+DnD\s+\d+[×x]\d+\s+Battlemap\s*$", "", title, flags=re.I)
    return title.strip()


def fetch_all_pages():
    max_pages = get_max_pages(SOURCE_ID, 25)
    max_age = get_scan_interval(SOURCE_ID, 7)
    pages = []
    for p in range(1, max_pages + 1):
        url = BASE_URL if p == 1 else f"{BASE_URL}page/{p}/"
        cache_name = f"seafoot-page-{p}.html"
        try:
            html = fetch_cached(url, cache_name, max_age_days=max_age)
            pages.append(html)
            if f"page/{p+1}/" not in html:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  Stopped at page {p}: {e}")
            break
    return pages


def extract_maps_from_page(html):
    soup = BeautifulSoup(html, "html.parser")
    maps = []
    for article in soup.select("article"):
        h = article.find(["h2", "h3"])
        if not h:
            continue
        a = h.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        title = clean_title(title)

        img = article.find("img")
        thumb = ""
        if img:
            thumb = img.get("data-src") or img.get("src") or ""

        entry = make_entry(SOURCE_ID, title, href, thumbnail_url=thumb)

        # Enrich with categories
        tags, env = parse_categories(article)
        if tags:
            entry["tags"] = tags
        if env:
            entry["environment"] = env

        maps.append(entry)
    return maps


def main():
    print(f"Grabbing {SOURCE_ID}...")
    pages = fetch_all_pages()
    print(f"  Fetched {len(pages)} pages")
    all_maps = []
    seen_ids = set()
    for html in pages:
        for m in extract_maps_from_page(html):
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                all_maps.append(m)
    print(f"  Total: {len(all_maps)} maps")
    save_index(SOURCE_ID, all_maps)


if __name__ == "__main__":
    main()
