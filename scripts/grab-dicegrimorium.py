#!/usr/bin/env python3
"""Grab plugin: Dice Grimorium free battlemaps.

Scrapes paginated WordPress blog → index/dice-grimorium.json
Only indexes metadata + thumbnail URL. Does NOT download images.
"""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index, guess_tags, get_max_pages, get_scan_interval
from bs4 import BeautifulSoup

SOURCE_ID = "dice-grimorium"
BASE_URL = "https://dicegrimorium.com/category/dnd-map/"


def clean_title(title):
    """Remove common suffixes and vol numbering noise."""
    title = re.sub(r"\s+D&D\s+Battle\s+Map\s*$", "", title, flags=re.I)
    title = re.sub(r"\s+DnD\s+Battle\s+Map\s*$", "", title, flags=re.I)
    return title.strip()


def fetch_all_pages():
    max_pages = get_max_pages(SOURCE_ID, 50)
    max_age = get_scan_interval(SOURCE_ID, 7)
    pages = []
    for p in range(1, max_pages + 1):
        url = BASE_URL if p == 1 else f"{BASE_URL}page/{p}/"
        cache_name = f"dicegrimorium-page-{p}.html"
        try:
            html = fetch_cached(url, cache_name, max_age_days=max_age)
            pages.append(html)
            if f"/page/{p+1}/" not in html:
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
        if "dicegrimorium.com" not in href:
            continue
        title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue

        title = clean_title(title)

        img = article.find("img")
        thumb = ""
        if img:
            thumb = img.get("data-src") or img.get("src") or ""

        entry = make_entry(SOURCE_ID, title, href, thumbnail_url=thumb)

        # Use grab_core guess_tags for environment/tags from title
        tags, env = guess_tags(title)
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
