"""Batch-download Wikipedia character images for the Spot the Intruder game.

Saves images to assets/images/heroes/<slug>.<ext>, skipping existing files.
"""

import os
import re
import time
import urllib.request
from pathlib import Path

SITE_ROOT = Path(__file__).resolve().parent.parent
HERO_DIR = SITE_ROOT / "assets" / "images" / "heroes"
HERO_DIR.mkdir(parents=True, exist_ok=True)

UA = {"User-Agent": "SocialGraphs/1.0 (educational project; course website)"}

# (node_id, wiki_page_title, preferred_filename_without_ext)
# wiki_page_title = what goes after /wiki/ in Wikipedia URL
CHARS = [
    ("Betsy_Braddock", "Betsy Braddock", "betsy-braddock"),
    ("Emma_Frost", "Emma Frost", "emma-frost"),
    ("Jean_Grey", "Jean Grey", "jean-grey"),
    ("Rachel_Summers", "Rachel Summers", "rachel-summers"),
    ("Storm_(Marvel_Comics)", "Storm (Marvel Comics)", "storm"),
    ("Cable_(character)", "Cable (character)", "cable"),
    ("Jubilee_(character)", "Jubilee (character)", "jubilee"),
    ("Scarlet_Witch", "Scarlet Witch", "scarlet-witch"),
    ("Spider-Woman", "Spider-Woman", "spider-woman"),
    ("Spider-Woman_(Gwen_Stacy)", "Spider-Woman (Gwen Stacy)", "spider-gwen"),
    ("Mayday_Parker", "Mayday Parker", "spider-girl"),
    ("Silk_(character)", "Silk (character)", "silk"),
    ("Black_Cat_(Marvel_Comics)", "Black Cat (Marvel Comics)", "black-cat"),
    ("Blade_(character)", "Blade (character)", "blade"),
    ("Ghost_Rider", "Ghost Rider (Johnny Blaze)", "ghost-rider"),
    ("Moon_Knight", "Moon Knight", "moon-knight"),
    ("Gwenpool", "Gwenpool", "gwenpool"),
    ("Venom_(character)", "Venom (character)", "venom"),
    ("Wolverine_(Ultimate_Marvel_character)", "Wolverine (Ultimate Marvel character)", "wolverine-ultimate"),
    ("Black_Widow_(Natasha_Romanova)", "Black Widow (Natasha Romanova)", "black-widow"),
    ("Iron_Fist_(character)", "Iron Fist (character)", "iron-fist"),
    ("Star-Lord", "Star-Lord", "star-lord"),
    ("Rocket_Raccoon", "Rocket Raccoon", "rocket-raccoon"),
    ("Hercules_(Marvel_Comics)", "Hercules (Marvel Comics)", "hercules-marvel"),
    ("Morbius", "Morbius (character)", "morbius"),
    ("Man-Thing", "Man-Thing", "man-thing"),
    ("Werewolf_by_Night", "Werewolf by Night", "werewolf-by-night"),
]


def fetch_infobox_image(wiki_title):
    """Return (image_url, ext) from the first infobox image on a Wikipedia page."""
    url = "https://en.wikipedia.org/wiki/" + wiki_title.replace(" ", "_")
    req = urllib.request.Request(url, headers=UA)
    html = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", errors="replace")

    # find infobox region
    m = re.search(r'class="infobox[^"]*"', html)
    if not m:
        return None, None
    chunk = html[m.start() - 50 : m.start() + 4000]
    imgs = re.findall(r'<img[^>]+src="([^"]+)"', chunk)
    if not imgs:
        return None, None

    raw = imgs[0]
    # remove html entities
    raw = raw.replace("&amp;", "&")
    # make absolute
    if raw.startswith("//"):
        raw = "https:" + raw
    elif raw.startswith("/"):
        raw = "https://en.wikipedia.org" + raw

    # guess extension from URL
    path = raw.split("?")[0]
    if path.lower().endswith(".webp"):
        ext = "webp"
    elif path.lower().endswith(".svg"):
        ext = "svg"
    elif path.lower().endswith(".png"):
        ext = "png"
    else:
        ext = "jpg"
    return raw, ext


def download_image(img_url, dest):
    req = urllib.request.Request(img_url, headers=UA)
    data = urllib.request.urlopen(req, timeout=30).read()
    with open(dest, "wb") as f:
        f.write(data)


def main():
    for node_id, wiki_title, slug in CHARS:
        # check for existing image (any extension)
        existing = list(HERO_DIR.glob(slug + ".*"))
        if existing:
            print(f"  SKIP {slug} ({existing[0].name} exists)")
            continue
        print(f"  Fetching {slug} ... ", end="", flush=True)
        for attempt in range(4):
            try:
                img_url, ext = fetch_infobox_image(wiki_title)
                if not img_url:
                    print("NO INFOBOX IMAGE")
                    break
                dest = HERO_DIR / f"{slug}.{ext}"
                download_image(img_url, dest)
                size = dest.stat().st_size
                print(f"OK ({size:,} bytes)")
                break
            except urllib.error.HTTPError as e:
                if e.code == 429:
                    wait = 5 * (attempt + 1)
                    print(f"429 - sleeping {wait}s...", flush=True)
                    time.sleep(wait)
                else:
                    print(f"HTTP {e.code}")
                    break
            except Exception as e:
                print(f"ERROR: {e}")
                break
        time.sleep(0.3)


if __name__ == "__main__":
    main()
