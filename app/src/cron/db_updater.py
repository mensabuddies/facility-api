# hydrate_facilities.py
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Reuse the same base directory convention as fetcher.py
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent  # same as in fetcher.py
sys.path.append(str(BASE_DIR))
FACILITIES_FILE = BASE_DIR / "assets" / "facilities.json"
FETCHED_DIR = BASE_DIR / "assets" / "fetched"

from app.src.config.database import engine

# --- Step 1: Load JSON & transform keys (detail_url -> detail_html, menu_url -> menu_html) ---

def transform_facility_item(item: Dict[str, Any]) -> Dict[str, Any]:
    """
    Return a copy of the facility dict with:
      - detail_url  -> detail_html (empty string)
      - menu_url    -> menu_html (empty string, only if menu_url existed)
    All other keys preserved, including id, address, description, etc.
    """
    transformed = dict(item)  # shallow copy

    # Replace detail_url -> detail_html
    if "detail_url" in transformed:
        transformed.pop("detail_url", None)
    transformed["detail_html"] = ""  # will be filled in Step 3

    # Replace menu_url -> menu_html only if menu_url existed
    had_menu_url = "menu_url" in item
    if had_menu_url:
        transformed.pop("menu_url", None)
        transformed["menu_html"] = ""  # will be filled in Step 3

    return transformed

def load_and_transform() -> List[Dict[str, Any]]:
    """
    Loads the JSON array and returns a new array with the same nesting:
    [
      {
        "organization_name": ...,
        "organization_domain": ...,
        "facilities": [
          {
            "location": ...,
            "canteens": [ { ... facility object ... }, ... ],
            "cafeterias": [ { ... facility object ... }, ... ]
          },
          ...
        ]
      },
      ...
    ]
    Where each facility object has detail_html/menu_html instead of URLs.
    """
    with open(FACILITIES_FILE, encoding="utf-8") as f:
        data = json.load(f)  # top-level list
    # Example shape verified from your facilities.json. :contentReference[oaicite:2]{index=2}

    out: List[Dict[str, Any]] = []
    for org in data:
        new_org = {
            "organization_name": org.get("organization_name"),
            "organization_domain": org.get("organization_domain"),
            "facilities": [],
        }
        for loc in org.get("facilities", []):
            new_loc = {
                "location": loc.get("location"),
                "canteens": [],
                "cafeterias": [],
            }
            for c in loc.get("canteens", []):
                new_loc["canteens"].append(transform_facility_item(c))
            for c in loc.get("cafeterias", []):
                new_loc["cafeterias"].append(transform_facility_item(c))
            new_org["facilities"].append(new_loc)
        out.append(new_org)

    return out

# --- Step 2: Find latest snapshot directory (assets/fetched/{YYYYMMDD_HHMMSS}) ---

def get_latest_snapshot_dir() -> Optional[Path]:
    """
    Returns the latest timestamped directory inside assets/fetched/, or None if none exist.
    The fetcher writes to this exact location with timestamped names. :contentReference[oaicite:3]{index=3}
    """
    if not FETCHED_DIR.exists():
        return None
    candidates = [p for p in FETCHED_DIR.iterdir() if p.is_dir()]
    if not candidates:
        return None
    # Names are sortable timestamps like 20250830_101500, so lexical sort works.
    return sorted(candidates)[-1]

# --- Step 3: Hydrate detail_html/menu_html from files in latest snapshot ---

def read_text_if_exists(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""

def hydrate_from_snapshot(objs: List[Dict[str, Any]], snapshot_dir: Optional[Path]) -> None:
    """
    In-place: for each facility (by id), read:
      snapshot_dir/{id}/detail.html -> detail_html
      snapshot_dir/{id}/menu.html   -> menu_html (if the key exists)
    The fetcher writes these filenames. :contentReference[oaicite:4]{index=4}
    """
    if snapshot_dir is None:
        return  # nothing to hydrate

    def hydrate_facility(f: Dict[str, Any]) -> None:
        fid = f.get("id")
        if not fid:
            return
        base = snapshot_dir / fid
        if "detail_html" in f:
            f["detail_html"] = read_text_if_exists(base / "detail.html")
        if "menu_html" in f:
            f["menu_html"] = read_text_if_exists(base / "menu.html")

    for org in objs:
        for loc in org.get("facilities", []):
            for canteen in loc.get("canteens", []):
                hydrate_facility(canteen)
            for cafeteria in loc.get("cafeterias", []):
                hydrate_facility(cafeteria)

# --- Step 4: Establish a database connection (no writes yet) ---

def connect_database():
    """
    Imports your configured SQLModel/SQLAlchemy engine and opens a connection.
    Uses connection string & engine from database.py. :contentReference[oaicite:5]{index=5}
    """

    # Open & close a connection to verify connectivity; no schema changes, no writes.
    conn = engine.connect()
    try:
        # no-op query that works across Postgres
        conn.execute("SELECT 1")
        print("✅ Database connection established.")
    finally:
        conn.close()

def main():
    # 1) Load & transform
    objs = load_and_transform()
    print("Loaded & transformed facilities.json")

    # 2) Locate latest snapshot
    latest = get_latest_snapshot_dir()
    if latest:
        print(f"Using latest snapshot: {latest}")
    else:
        print("No snapshot directory found; leaving HTML fields empty.")

    # 3) Hydrate HTML fields
    hydrate_from_snapshot(objs, latest)

    # (Optional) you can inspect or serialize the hydrated structure here
    print(json.dumps(objs, ensure_ascii=False, indent=2))

    # 4) Connect to DB
    connect_database()

if __name__ == "__main__":
    main()
