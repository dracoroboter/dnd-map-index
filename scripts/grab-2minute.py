#!/usr/bin/env python3
"""Grab plugin: 2-Minute Tabletop free maps.

Scrapes paginated WooCommerce product listing → index/2minute-tabletop.json
Note: only indexes metadata + thumbnail URL. Does NOT download images.
Download policy for this source is link_to_source (CC BY-NC 4.0).
"""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index
from bs4 import BeautifulSoup

SOURCE_ID = "2minute-tabletop"
BASE_URL = "https://2minutetabletop.com/product-category/free/"
MAX_PAGES = 30  # safety limit

def fetch_all_pages():
    """Fetch all paginated listing pages."""
    pages = []
    for p in range(1, MAX_PAGES + 1):
        url = BASE_URL if p == 1 else f"{BASE_URL}page/{p}/"
        cache_name = f"2minute-page-{p}.html"
        try:
            html = fetch_cached(url, cache_name)
            pages.append(html)
            # stop if this page has no "next" link
            if f"page/{p+1}/" not in html:
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  Stopped at page {p}: {e}")
            break
    return pages

def extract_maps_from_page(html):
    """Extract map entries from a single listing page."""
    soup = BeautifulSoup(html, "html.parser")
    maps = []
    # WooCommerce product items
    for li in soup.select("li.product, div.product"):
        a = li.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if "2minutetabletop.com/product/" not in href:
            continue
        # title from heading or link text
        h2 = li.find("h2")
        title = h2.get_text(strip=True) if h2 else ""
        if not title:
            title = a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        # skip non-map products
        lower = title.lower()
        if any(skip in lower for skip in ["everything pack", "token", "handbook"]):
            continue
        # thumbnail from img
        img = li.find("img")
        thumb = ""
        if img:
            # prefer srcset smallest, or src
            thumb = img.get("src", "")
            # WooCommerce often has -300x300 in thumbnail URL
        entry = make_entry(SOURCE_ID, title, href, thumbnail_url=thumb)
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
    save_index(SOURCE_ID, all_maps)

if __name__ == "__main__":
    main()
