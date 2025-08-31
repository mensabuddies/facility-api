import json
import sys
from pathlib import Path
from typing import Optional

# --- Locate project root (dir containing "app") and prepend to sys.path ---
_PROJECT_ROOT: Optional[Path] = None
_probe = Path(__file__).resolve()
for _ in range(6):
    if (_probe / "app").is_dir():
        _PROJECT_ROOT = _probe
        break
    _probe = _probe.parent

BASE_DIR = _PROJECT_ROOT or Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

FACILITIES_FILE = BASE_DIR / "assets" / "facilities.json"
FETCHED_DIR = BASE_DIR / "assets" / "fetched"

# Import the Pydantic models
from app.src.cron.db_updater.schema import (  # adjust path if you placed them elsewhere
    FacilitiesRoot,
    OrganizationBlock,
    LocationFacilities,
    Facility,
)

class ContentLoader:
    # --- Step 1: Load JSON & build Pydantic models (urls -> *_html handled in from_json_item) ---
    def _load_models(self) -> FacilitiesRoot:
        data = json.loads(FACILITIES_FILE.read_text(encoding="utf-8"))
        # Build typed models from the raw JSON
        orgs = [OrganizationBlock.from_json_item(x) for x in data]
        return FacilitiesRoot(organizations=orgs)

    # --- Step 2: Find latest snapshot directory (assets/fetched/{YYYYMMDD_HHMMSS}) ---
    def _get_latest_snapshot_dir(self) -> Optional[Path]:
        if not FETCHED_DIR.exists():
            return None
        dirs = [p for p in FETCHED_DIR.iterdir() if p.is_dir()]
        return sorted(dirs, key=lambda p: p.name)[-1] if dirs else None

    # --- Step 3: Hydrate detail_html/menu_html from files in latest snapshot ---
    def _read_text_if_exists(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return ""

    def _hydrate_from_snapshot(self, root: FacilitiesRoot, snapshot_dir: Optional[Path]) -> None:
        if snapshot_dir is None:
            return

        for facility in root.all_facilities():
            base = snapshot_dir / facility.id
            detail = base / "detail.html"
            menu = base / "menu.html"

            if detail.exists():
                facility.detail_html = self._read_text_if_exists(detail)

            # Only hydrate menu_html if the facility originally had a menu_url
            if facility.menu_html is not None and menu.exists():
                facility.menu_html = self._read_text_if_exists(menu)

    # --- Public API ---
    def load_content(self) -> FacilitiesRoot:
        # 1) Load & build Pydantic models
        root = self._load_models()
        print("Loaded facilities.json into Pydantic models")

        # 2) Locate latest snapshot
        latest = self._get_latest_snapshot_dir()
        if latest:
            print(f"Using latest snapshot: {latest}")
        else:
            print("No snapshot directory found; leaving HTML fields empty.")

        # 3) Hydrate HTML fields in-place
        self._hydrate_from_snapshot(root, latest)

        # Optional: debug print as JSON (Pydantic v2: model_dump; v1: dict)
        # try:
        #     print(json.dumps(root.model_dump(), ensure_ascii=False, indent=2))
        # except AttributeError:
        #     print(json.dumps(root.dict(), ensure_ascii=False, indent=2))

        return root
