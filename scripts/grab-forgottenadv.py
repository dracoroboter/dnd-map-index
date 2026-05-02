#!/usr/bin/env python3
"""Grab plugin: Forgotten Adventures free battlemaps.

Scrapes paginated WooCommerce product listing → index/forgotten-adventures.json
Only indexes FREE battlemaps. Does NOT download images.
"""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index, guess_tags, get_max_pages, get_scan_interval
from bs4 import BeautifulSoup

SOURCE_ID = "forgotten-adventures"
BASE_URL = "https://www.forgotten-adventures.net/product-category/battlemaps/"


def clean_title(title):
    """Remove grid size suffix."""
    return re.sub(r"\s*\[\d+[×xX]\d+\]\s*$", "", title).strip()


def fetch_all_pages():
    max_pages = get_max_pages(SOURCE_ID, 10)
    max_age = get_scan_interval(SOURCE_ID, 14)
    pages = []
    for p in range(1, max_pages + 1):
        url = BASE_URL if p == 1 else f"{BASE_URL}page/{p}/"
        cache_name = f"forgottenadv-page-{p}.html"
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


def extract_free_maps(html):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find("div", class_="products")
    if not container:
        return []
    maps = []
    for div in container.find_all("div", class_="product-small", recursive=False):
        # Check if free
        price_el = div.find(class_="price") or div.find(class_="amount")
        price_text = price_el.get_text(strip=True) if price_el else ""
        if "free" not in price_text.lower():
            continue

        # Title
        h2 = div.find("h2") or div.find(class_="name")
        if not h2:
            continue
        a = h2.find("a", href=True)
        title = a.get_text(strip=True) if a else h2.get_text(strip=True)
        href = a["href"] if a else ""
        if not title or not href:
            continue

        title = clean_title(title)

        # Thumbnail
        img = div.find("img")
        thumb = ""
        if img:
            thumb = img.get("data-src") or img.get("src") or ""

        entry = make_entry(SOURCE_ID, title, href, thumbnail_url=thumb)

        tags, env = guess_tags(title)
        if tags:
            entry["tags"] = tags
        if env:
            entry["environment"] = env

        maps.append(entry)
    return maps


def main():
    print(f"Grabbing {SOURCE_ID} (free maps only)...")
    pages = fetch_all_pages()
    print(f"  Fetched {len(pages)} pages")
    all_maps = []
    seen_ids = set()
    for html in pages:
        for m in extract_free_maps(html):
            if m["id"] not in seen_ids:
                seen_ids.add(m["id"])
                all_maps.append(m)
    print(f"  Total: {len(all_maps)} free maps (skipped paid)")
    save_index(SOURCE_ID, all_maps)


if __name__ == "__main__":
    main()
