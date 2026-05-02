#!/usr/bin/env python3
"""Grab plugin: Tom Cartos fantasy battlemaps.

Scrapes tomcartos.com gallery (Squarespace) → index/tom-cartos.json
Two-level crawl: /map-gallery → category sub-pages → individual map entries.
Only indexes metadata + thumbnail URL. Does NOT download images.
"""

import re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index
from bs4 import BeautifulSoup

SOURCE_ID = "tom-cartos"
GALLERY_URL = "https://www.tomcartos.com/map-gallery"
BASE = "https://www.tomcartos.com"

# Sub-pages to skip (not battlemaps, or modular/asset content)
SKIP_SLUGS = {
    "cartosia-region-map",              # region overview, not a battlemap
    "build-a-bastion",                  # modular tile set
    "modular-dungeon-tiles",            # modular tile set
    "modular-terrain-sets",             # modular tile set
    "into-the-wilds-illustrations",     # illustrations, not battlemaps
}

# Individual map titles to skip (illustrations, characters, tokens)
SKIP_TITLE_PATTERNS = [
    r"\billustration\b",
    r"\bcharacters? of\b",
    r"\btoken\b",
]

# Navigation/menu paths to ignore when extracting category links
NAV_PATHS = {
    "/", "/cart", "/home-1", "/gallery-1", "/map-gallery", "/asset-gallery",
    "/modern-map-gallery", "/modern-asset-gallery", "/token-gallery",
    "/adventure-gallery", "/more", "/itw-preview", "/newsletter",
    "/about-patreon", "/commercial-licensing", "/toms-open-map-license",
    "/using-myairbridge", "/faq", "/my-links", "/contact-me",
}


def is_skip_title(title):
    t = title.lower()
    return any(re.search(p, t) for p in SKIP_TITLE_PATTERNS)


def extract_category_links(html):
    """Extract category sub-page paths from the gallery overview."""
    soup = BeautifulSoup(html, "html.parser")
    links = set()
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href.startswith("/") or href.startswith("//"):
            continue
        slug = href.strip("/")
        if href in NAV_PATHS or slug in SKIP_SLUGS:
            continue
        # Only internal paths (no query strings, no anchors)
        if "?" in href or "#" in href:
            continue
        # Must be a simple /slug path (one level)
        if href.count("/") > 1:
            continue
        # Skip external-looking or known non-category patterns
        if slug.startswith(("http", "mailto")):
            continue
        links.add(href)
    return sorted(links)


def extract_maps_from_category(html, category_url):
    """Extract individual map entries from a category sub-page."""
    soup = BeautifulSoup(html, "html.parser")
    maps = []

    # Pattern 1: gallery grid items with clickthrough links (settlements, places of interest)
    seen_hrefs = set()
    for item in soup.select(".gallery-grid-item.has-clickthrough"):
        a = item.find("a", href=True)
        if not a:
            continue
        href = a["href"]
        if href in seen_hrefs:
            continue
        seen_hrefs.add(href)

        caption = item.select_one(".gallery-caption, .slide-title")
        title = caption.get_text(strip=True) if caption else ""
        if not title or len(title) < 3:
            continue
        if is_skip_title(title):
            continue

        img = item.find("img")
        thumb = ""
        if img:
            thumb = img.get("data-src") or img.get("src") or ""

        source_url = BASE + href if href.startswith("/") else href
        entry = make_entry(SOURCE_ID, title, source_url, thumbnail_url=thumb)
        maps.append(entry)

    # Pattern 2: Into the Wilds pages — sections with title + images, no clickthrough
    if not maps:
        for section in soup.select("section.page-section"):
            strong = section.find("strong")
            if not strong:
                continue
            title = strong.get_text(strip=True)
            if not title or not re.search(r"\d{2}$", title):
                continue
            if is_skip_title(title):
                continue
            imgs = [img for img in section.find_all("img")
                    if "squarespace-cdn" in (img.get("data-src") or img.get("src") or "")]
            thumb = ""
            if imgs:
                thumb = imgs[0].get("data-src") or imgs[0].get("src") or ""
            entry = make_entry(SOURCE_ID, title, category_url, thumbnail_url=thumb)
            maps.append(entry)

    return maps


def main():
    print(f"Grabbing {SOURCE_ID}...")

    # Step 1: fetch gallery overview
    gallery_html = fetch_cached(GALLERY_URL, "tomcartos-gallery.html")
    category_paths = extract_category_links(gallery_html)
    print(f"  Found {len(category_paths)} category pages")

    # Step 2: fetch each category and extract maps
    all_maps = []
    seen_ids = set()

    for path in category_paths:
        url = BASE + path
        slug = path.strip("/")
        cache_name = f"tomcartos-{slug}.html"
        try:
            html = fetch_cached(url, cache_name)
            maps = extract_maps_from_category(html, url)
            new = 0
            for m in maps:
                if m["id"] not in seen_ids:
                    seen_ids.add(m["id"])
                    all_maps.append(m)
                    new += 1
            if new:
                print(f"    {slug}: {new} maps")
            time.sleep(0.3)
        except Exception as e:
            print(f"    {slug}: ERROR {e}")

    print(f"  Total: {len(all_maps)} maps")
    save_index(SOURCE_ID, all_maps)


if __name__ == "__main__":
    main()
