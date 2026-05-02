#!/usr/bin/env python3
"""Grab plugin: Dyson Logos commercial maps.

Scrapes dysonlogos.blog/maps/commercial-maps/ → index/dyson-logos.json
"""

import re, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index, slugify
from bs4 import BeautifulSoup

SOURCE_ID = "dyson-logos"
INDEX_URL = "https://dysonlogos.blog/maps/commercial-maps/"

SKIP_PATHS = [
    "/about/", "/tag/", "/category/", "/downloads", "/house-rules",
    "/characters", "/maps/commercial", "/maps/tutorials", "/maps/adventures",
    "/maps/cities", "/maps/inns", "/maps/multi-page", "/maps/geomorph",
    "/maps/vertical", "/maps/sewers", "/maps/kevin", "/zerobarrier",
    "/maps/the-dyson", "/maps/dysons-delve", "/maps/erdea",
    "/colour-portfolio", "/shadows-of",
]

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
        img = a.find("img")
        title = ""
        thumb = ""
        if img:
            title = img.get("alt", "").strip()
            src = img.get("src", "")
            if src:
                thumb = re.sub(r"\?w=\d+", "?w=200", src)
                if "?w=" not in thumb:
                    thumb += "?w=200"
        if not title:
            title = a.get("title", "").strip() or a.get_text(strip=True)
        if not title or len(title) < 3:
            continue
        title = re.sub(r"\s*\(?\d+\s*dpi\)?\s*$", "", title, flags=re.I).strip()
        entry = make_entry(SOURCE_ID, title, href, thumbnail_url=thumb)
        if entry["id"] not in seen:
            maps.append(entry)
    return maps

def main():
    html = fetch_cached(INDEX_URL, "dyson-commercial-maps.html")
    maps = extract_maps(html)
    save_index(SOURCE_ID, maps)

if __name__ == "__main__":
    main()
