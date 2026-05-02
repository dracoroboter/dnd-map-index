#!/usr/bin/env python3
"""Grab plugin: Reddit r/battlemaps (experimental).

Two modes:
  - Public API (no auth): ~300 top posts. Works out of the box.
  - Authenticated API: full pagination, ~5000-10000 maps. Requires .env file.

Setup auth: see docs/reddit-api-setup.md

Policy compliance:
  - No image downloads (metadata + remote thumbnail URL only)
  - Thumbnails: Reddit preview URLs (already public)
  - Source URL: link to original Reddit post
  - License: all-rights-reserved (default, per-post)
"""

import json, os, re, sys, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from grab_core import fetch_cached, make_entry, save_index, slugify, CACHE_DIR, ROOT, get_max_pages, get_scan_interval
import requests

SOURCE_ID = "reddit-curated"
SUBREDDIT = "battlemaps"
UA = "dnd-map-index/0.2 (personal project, https://github.com/dracoroboter/dnd-map-index)"

# ── Flair → tags/environment mapping ─────────────────────────────

FLAIR_MAP = {
    "fantasy - interior": (["interior", "building"], "house"),
    "fantasy - town/city": (["town", "settlement"], "town"),
    "fantasy - dungeon": (["dungeon"], "dungeon"),
    "fantasy - vehicle/ship": (["ship", "naval"], "ship"),
    "forest": (["forest", "natural"], "forest"),
    "caves/underground": (["cave", "natural"], "cave"),
    "mountain/hills": (["mountain"], "mountain"),
    "jungle/swamp": (["swamp", "natural"], "swamp"),
    "sea/coast": (["coastal"], "coast"),
    "desert": (["desert"], "desert"),
    "otherworldly": (["otherworldly"], "dungeon"),
    "arctic/snow": (["winter"], "mountain"),
    "river/bridge": (["river", "bridge"], "river"),
    "plains": (["plains"], "road"),
    "other map": ([], "dungeon"),
    "modern - interior": (["modern", "interior"], "house"),
    "modern - vehicle/ship": (["modern", "ship"], "ship"),
}

SKIP_FLAIRS = {"misc. - resource / guide", "question", "discussion", "meta"}

# ── Auth ─────────────────────────────────────────────────────────

def load_env():
    """Load .env file if present. Returns dict or empty."""
    env_file = ROOT / ".env"
    if not env_file.exists():
        return {}
    env = {}
    for line in env_file.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()
    return env


def get_auth_token(env):
    """Get OAuth2 token from Reddit. Returns token string or None."""
    cid = env.get("REDDIT_CLIENT_ID", "")
    secret = env.get("REDDIT_CLIENT_SECRET", "")
    user = env.get("REDDIT_USERNAME", "")
    pwd = env.get("REDDIT_PASSWORD", "")
    if not all([cid, secret, user, pwd]):
        return None
    auth = requests.auth.HTTPBasicAuth(cid, secret)
    data = {"grant_type": "password", "username": user, "password": pwd}
    r = requests.post("https://www.reddit.com/api/v1/access_token",
                       auth=auth, data=data,
                       headers={"User-Agent": UA}, timeout=15)
    r.raise_for_status()
    token = r.json().get("access_token")
    return token

# ── Helpers ──────────────────────────────────────────────────────

def clean_title(title):
    title = re.sub(r"\[?\d+\s*[×xX]\s*\d+\]?", "", title)
    title = re.sub(r"\[OC\]", "", title, flags=re.I)
    title = re.sub(r"\s*\|\s*", " - ", title)
    title = re.sub(r"\s{2,}", " ", title)
    return title.strip().rstrip("-").strip()


def get_thumbnail(post):
    preview = post.get("preview", {})
    images = preview.get("images", [])
    if images:
        resolutions = images[0].get("resolutions", [])
        for r in reversed(resolutions):
            if r.get("width", 0) <= 640:
                return r["url"].replace("&amp;", "&")
        src = images[0].get("source", {}).get("url", "")
        return src.replace("&amp;", "&")
    thumb = post.get("thumbnail", "")
    return thumb if thumb.startswith("http") else ""


def post_to_entry(post):
    """Convert a Reddit post dict to a map entry, or None if not a map."""
    flair = (post.get("link_flair_text") or "").strip()
    if flair.lower() in SKIP_FLAIRS:
        return None
    if post.get("is_self") and not post.get("preview"):
        return None

    title = post.get("title", "")
    if not title or len(title) < 5:
        return None
    title = clean_title(title)
    if not title:
        return None

    permalink = post.get("permalink", "")
    if not permalink:
        return None
    source_url = f"https://www.reddit.com{permalink}"

    entry = make_entry(SOURCE_ID, title, source_url, thumbnail_url=get_thumbnail(post))
    entry["author"] = post.get("author", "unknown")
    entry["reddit_score"] = post.get("score", 0)

    flair_lower = flair.lower()
    if flair_lower in FLAIR_MAP:
        tags, env = FLAIR_MAP[flair_lower]
        if tags:
            entry["tags"] = list(tags)
        if env:
            entry["environment"] = env

    return entry

# ── Public API (no auth) ─────────────────────────────────────────

def grab_public():
    """Fetch top posts via public JSON API. ~300 maps max."""
    print("  Mode: public API (no auth, limited to ~300 posts)")
    listings = [
        ("top", {"t": "all", "limit": 100}),
        ("top", {"t": "year", "limit": 100}),
        ("top", {"t": "month", "limit": 100}),
    ]
    all_maps = []
    seen = set()
    max_age = get_scan_interval(SOURCE_ID, 1)
    for sort, params in listings:
        url = f"https://www.reddit.com/r/{SUBREDDIT}/{sort}.json"
        cache_name = f"reddit-{sort}-{params.get('t', 'hot')}.json"
        CACHE_DIR.mkdir(exist_ok=True)
        cache_file = CACHE_DIR / cache_name
        use_cache = False
        if cache_file.exists():
            import os
            age_days = (time.time() - os.path.getmtime(cache_file)) / 86400
            if age_days <= max_age:
                use_cache = True
        if use_cache:
            print(f"  Using cached {cache_name}")
            data = json.loads(cache_file.read_text(encoding="utf-8"))
        else:
            print(f"  Fetching {sort}/t={params.get('t')}...")
            r = requests.get(url, params=params,
                             headers={"User-Agent": UA}, timeout=30)
            r.raise_for_status()
            data = r.json()
            cache_file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        for child in data.get("data", {}).get("children", []):
            entry = post_to_entry(child["data"])
            if entry and entry["id"] not in seen:
                seen.add(entry["id"])
                all_maps.append(entry)
        time.sleep(1)
    return all_maps

# ── Authenticated API (full pagination) ──────────────────────────

def grab_authenticated(token):
    """Fetch ALL top posts via authenticated API with pagination."""
    print("  Mode: authenticated API (full pagination)")
    headers = {"Authorization": f"bearer {token}", "User-Agent": UA}
    base_url = f"https://oauth.reddit.com/r/{SUBREDDIT}/top"

    all_maps = []
    seen = set()
    after = None
    page = 0
    max_pages = get_max_pages(SOURCE_ID, 200)

    while page < max_pages:
        params = {"t": "all", "limit": 100}
        if after:
            params["after"] = after

        try:
            r = requests.get(base_url, params=params, headers=headers, timeout=30)
            r.raise_for_status()
            data = r.json()
        except Exception as e:
            print(f"  Stopped at page {page}: {e}")
            break

        children = data.get("data", {}).get("children", [])
        if not children:
            break

        new = 0
        for child in children:
            entry = post_to_entry(child["data"])
            if entry and entry["id"] not in seen:
                seen.add(entry["id"])
                all_maps.append(entry)
                new += 1

        page += 1
        after = data["data"].get("after")
        if page % 10 == 0:
            print(f"    Page {page}: {len(all_maps)} maps so far")

        if not after:
            break
        time.sleep(0.6)  # ~100 req/min limit

    print(f"  Fetched {page} pages")
    return all_maps

# ── Main ─────────────────────────────────────────────────────────

def main():
    print(f"Grabbing {SOURCE_ID} (experimental)...")
    env = load_env()
    token = None

    if env.get("REDDIT_CLIENT_ID"):
        try:
            token = get_auth_token(env)
            if token:
                print("  Auth: OK")
        except Exception as e:
            print(f"  Auth failed ({e}), falling back to public API")

    if token:
        all_maps = grab_authenticated(token)
    else:
        all_maps = grab_public()

    # Sort by score descending
    all_maps.sort(key=lambda m: m.get("reddit_score", 0), reverse=True)

    print(f"  Total: {len(all_maps)} maps")
    save_index(SOURCE_ID, all_maps)


if __name__ == "__main__":
    main()
