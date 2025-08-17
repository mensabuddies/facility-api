import os
import json
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

"""
1. Loads facilities.json.
2. Creates a new timestamped folder under assets/fetched/.
3. Iterates through each facility.
4. For each canteen/cafeteria:
   - Creates a folder named with its id.
   - Downloads the raw HTML from detail_url (and menu_url if present).
   - Extracts only the <main>...</main> section.
   - Saves them as detail.html and/or menu.html.
"""

# Path setup
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
print(BASE_DIR)
FACILITIES_FILE = BASE_DIR / "assets" / "facilities.json"
FETCHED_DIR = BASE_DIR / "assets" / "fetched"

def fetch_html(url: str) -> str | None:
    """Fetch HTML and return only the <div class="gastronomy"> content, cleaned."""
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # 1. Find <main>
        main = soup.find("main")
        if not main:
            return None

        # 2. Find <div class="gastronomy"
        gastronomy = main.find("div", class_="gastronomy")
        if not gastronomy:
            return None

        # 3. Remove unwanted sections - currently:
        # - <div class="gallery">
        # - <div class="gastronomy-detail_bottom">
        for unwanted in gastronomy.find_all("div", class_=["gallery", "gastronomy-detail_bottom"]):
            unwanted.decompose()

        # 4. Remove all <script> tags
        for script in gastronomy.find_all("script"):
            script.decompose()

        return str(gastronomy)

    except Exception as e:
        print(f"❌ Failed to fetch {url}: {e}")
        return None



def save_html(content: str, path: Path):
    """Save HTML string to file."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def process_facility(item: dict, base_outdir: Path):
    """Process a single facility (canteen or cafeteria)."""
    id = item.get("id")
    if not id:
        print("⚠️ Skipping facility without id")
        return

    facility_dir = base_outdir / id
    facility_dir.mkdir(parents=True, exist_ok=True)

    # Detail page
    detail_url = item.get("detail_url")
    if detail_url:
        detail_html = fetch_html(detail_url)
        if detail_html:
            save_html(detail_html, facility_dir / "detail.html")

    # Menu page (if exists)
    menu_url = item.get("menu_url")
    if menu_url:
        menu_html = fetch_html(menu_url)
        if menu_html:
            save_html(menu_html, facility_dir / "menu.html")

def main():
    # Timestamp folder
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outdir = FETCHED_DIR / timestamp
    outdir.mkdir(parents=True, exist_ok=True)

    # Load facilities.json
    with open(FACILITIES_FILE, encoding="utf-8") as f:
        data = json.load(f)

    for org in data:
        for location in org.get("facilities", []):
            for canteen in location.get("canteens", []):
                process_facility(canteen, outdir)
            for cafeteria in location.get("cafeterias", []):
                process_facility(cafeteria, outdir)

    print(f"✅ Finished fetching facilities into {outdir}")

if __name__ == "__main__":
    main()
