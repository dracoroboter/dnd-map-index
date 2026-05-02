#!/usr/bin/env python3
"""Scrape Dyson Logos commercial-maps page → index JSON with titles and URLs."""

import json, re, sys, time
from pathlib import Path
from urllib.parse import urlparse

try:
    import requests
    from bs4 import BeautifulSoup
except ImportError:
    sys.exit("pip install requests beautifulsoup4")

INDEX_URL = "https://dysonlogos.blog/maps/commercial-maps/"
OUT = Path(__file__).resolve().parent.parent / "index" / "dyson-logos.json"
CACHE = Path(__file__).resolve().parent.parent / ".cache"

def slugify(title):
    s = title.lower().strip()
    s = re.sub(r"[''']s\b", "s", s)
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")

def fetch_page(url):
    CACHE.mkdir(exist_ok=True)
    cache_file = CACHE / "commercial-maps.html"
    if cache_file.exists():
        print(f"Using cached {cache_file}")
        return cache_file.read_text(encoding="utf-8")
    print(f"Fetching {url} ...")
    r = requests.get(url, headers={"User-Agent": "dnd-map-index/0.1 (personal project)"}, timeout=30)
    r.raise_for_status()
    cache_file.write_text(r.text, encoding="utf-8")
    return r.text

SKIP_PATHS = {
    "/about/", "/tag/", "/category/", "/downloads", "/house-rules",
    "/characters", "/maps/commercial", "/maps/tutorials", "/maps/adventures",
    "/maps/cities", "/maps/inns", "/maps/multi-page", "/maps/geomorph",
    "/maps/vertical", "/maps/sewers", "/maps/kevin", "/zerobarrier",
    "/maps/the-dyson", "/maps/dysons-delve", "/maps/erdea",
    "/colour-portfolio", "/shadows-of",
}

def is_map_link(href):
    if "dysonlogos.blog" not in href and "rpgcharacters.wordpress" not in href:
        return False
    if any(skip in href for skip in SKIP_PATHS):
        return False
    if "#comment" in href or "patreon" in href or "drivethrurpg" in href:
        return False
    if href.startswith("mailto:"):
        return False
    if href.rstrip("/").endswith("/maps"):
        return False
    return True

def extract_maps(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.select_one("div.post-content") or soup.find("article")
    if not content:
        sys.exit("Cannot find content div")
    maps = []
    seen = set()
    for a in content.find_all("a", href=True):
        href = a["href"]
        if not is_map_link(href) or href in seen:
            continue
        seen.add(href)
        # title from img alt, or link text, or link title attr
        img = a.find("img")
        title = ""
        if img:
            title = img.get("alt", "").strip()
        if not title:
            title = a.get("title", "").strip() or a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        # clean up title
        title = re.sub(r"\s*\(?\d+\s*dpi\)?\s*$", "", title, flags=re.I).strip()
        slug = f"dyson-logos-{slugify(title)}"
        maps.append({
            "id": slug,
            "title": title,
            "author": "Dyson Logos",
            "source_url": href,
            "image_url": "",
            "license": {
                "type": "commercial-free",
                "attribution": "Cartography by Dyson Logos"
            },
            "tags": [],
            "environment": "",
            "map_type": "battlemap",
            "style": "bw-ink",
            "format": "png",
            "status": "new",
            "date_indexed": time.strftime("%Y-%m-%d")
        })
    return maps

def main():
    html = fetch_page(INDEX_URL)
    maps = extract_maps(html)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(maps, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Extracted {len(maps)} maps → {OUT}")

if __name__ == "__main__":
    main()
