from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional
import re

def _clean_text(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()

# --- weekday helpers ----------------------------------------------------------

_DAY_ORDER = ["montag", "dienstag", "mittwoch", "donnerstag", "freitag", "samstag", "sonntag"]
_DAY_KEY   = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
_ALIASES = {
    "mo": "montag", "di": "dienstag", "mi": "mittwoch", "do": "donnerstag",
    "fr": "freitag", "sa": "samstag", "so": "sonntag",
}

def _norm_day_token(tok: str) -> Optional[str]:
    t = re.sub(r"[.\s]+", "", tok.lower())  # "Mo." -> "mo"
    t = _ALIASES.get(t, t)
    return t if t in _DAY_ORDER else None

def _expand_days(label: str) -> List[int]:
    """
    Expand a label like:
      - "Montag - Freitag" / "Montag – Freitag" / "Montag bis Freitag"
      - "Montag, Mittwoch und Freitag"
      - "Samstag/Sonntag"
    into a list of day indices (0=Mon .. 6=Sun).
    """
    text = _clean_text(label).lower()
    parts = re.split(r"\s*(?:,|und|/|;)\s*", text)  # split lists first

    idxs: List[int] = []
    for part in parts:
        rng = re.split(r"\s*(?:-|–|bis)\s*", part)  # handle ranges
        if len(rng) == 1:
            d = _norm_day_token(rng[0])
            if d is not None:
                idxs.append(_DAY_ORDER.index(d))
        elif len(rng) == 2:
            a, b = _norm_day_token(rng[0]), _norm_day_token(rng[1])
            if a is None or b is None:
                continue
            ia, ib = _DAY_ORDER.index(a), _DAY_ORDER.index(b)
            if ia <= ib:
                idxs.extend(range(ia, ib + 1))
            else:  # wraparound (rare)
                idxs.extend(list(range(ia, 7)) + list(range(0, ib + 1)))
    # de-dup preserve order
    seen, out = set(), []
    for i in idxs:
        if i not in seen:
            seen.add(i); out.append(i)
    return out

def _empty_by_day_slots() -> Dict[str, List[Dict[str, str]]]:
    return {k: [] for k in _DAY_KEY}

def _empty_by_day_compact() -> Dict[str, Dict[str, Optional[str]]]:
    return {k: {"opens": None, "closes": None, "food_until": None} for k in _DAY_KEY}

def _state_text_without_icon(state_el) -> Optional[str]:
    if not state_el:
        return None
    for sp in state_el.select(".icon-mi, .icon-mi-filled"):
        sp.extract()
    return _clean_text(state_el.get_text())

# --- time parsing helpers -----------------------------------------------------

_TIME_RE = re.compile(r"(\d{1,2})[:.](\d{2})")  # 8:30 / 08.30

def _norm_hhmm(s: str) -> Optional[str]:
    """Return 'HH:MM' or None."""
    m = _TIME_RE.search(s)
    if not m:
        return None
    h, mnt = int(m.group(1)), int(m.group(2))
    if 0 <= h <= 23 and 0 <= mnt <= 59:
        return f"{h:02d}:{mnt:02d}"
    return None

def _parse_time_range(text: str) -> tuple[Optional[str], Optional[str]]:
    """Parse '08:30 - 15:00 Uhr' into ('08:30','15:00')."""
    # normalize separators, remove 'Uhr'
    t = text.replace("Uhr", "")
    # split on -, – or to dash variants
    parts = re.split(r"\s*(?:-|–|—|bis)\s*", t)
    if len(parts) >= 2:
        o = _norm_hhmm(parts[0])
        c = _norm_hhmm(parts[1])
        return o, c
    # fallback: single time only (rare)
    single = _norm_hhmm(t)
    return (single, None)

def _extract_food_until(meta: str) -> Optional[str]:
    """
    Extract time from meta like 'Essensausgabe bis 14:45 Uhr' -> '14:45'.
    Loosely searches for 'bis <time>'.
    """
    if not meta:
        return None
    # remove 'Uhr' and look for a time after 'bis'
    s = meta.replace("Uhr", "")
    # Prefer a 'bis <time>' capture
    m = re.search(r"\bbis\b.*?(\d{1,2}[:.]\d{2})", s, flags=re.IGNORECASE)
    if m:
        return _norm_hhmm(m.group(1))
    # fallback: any time in string
    return _norm_hhmm(s)

# --- main parser --------------------------------------------------------------

def parse_html_detail(html: str) -> Dict[str, Any]:
    """
    Detail page → notices (HTML), opening times by ranges AND per-day compact fields:
      opening_times.by_day = { monday: {opens, closes, food_until}, ... }
    """
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".gastronomy")
    if not root:
        return {
            "notices_html": [],
            "opening_times": {
                "state": None,
                "ranges": [],
                "by_day": _empty_by_day_compact(),
            },
        }

    # Notices (keep HTML)
    notices_html: List[str] = []
    for n in root.select(".notice"):
        for icon in n.select(".icon-mi, .icon-mi-filled"):
            icon.extract()
        content_html = n.decode_contents().strip()
        if content_html:
            notices_html.append(content_html)

    # Opening times block
    opening = root.select_one(".opening-times_detail")
    state_text = _state_text_without_icon(opening.select_one(".opening-time_state")) if opening else None

    def extract_time_blocks(scope) -> List[Dict[str, str]]:
        blocks: List[Dict[str, str]] = []
        if not scope:
            return blocks
        for ot in scope.select(".opening-time"):
            t = ot.select_one(".opening-times__time")
            m = ot.select_one(".opening-times__meta")
            blocks.append({
                "time": _clean_text(t.get_text()) if t else "",
                "meta": _clean_text(m.get_text()) if m else "",
            })
        return blocks

    ranges: List[Dict[str, Any]] = []
    if opening:
        for rng in opening.select(".opening-time_listing-all .opening-time_days"):
            days_el = rng.select_one(".opening-time-day-range")
            days_label = _clean_text(days_el.get_text()) if days_el else _clean_text(rng.get_text())
            times = extract_time_blocks(rng.select_one(".opening-time_set"))
            ranges.append({"days": days_label, "times": times})

    # Expand to per-day *slots* first (so we can merge easily)
    day_slots = _empty_by_day_slots()
    for r in ranges:
        day_idxs = _expand_days(r["days"])
        for di in day_idxs:
            key = _DAY_KEY[di]
            for slot in r["times"] or []:
                # push normalized slot
                opens, closes = _parse_time_range(slot.get("time", ""))
                food_until = _extract_food_until(slot.get("meta", ""))
                day_slots[key].append({
                    "opens": opens, "closes": closes, "food_until": food_until
                })

    # Merge multiple slots → single opens/closes/food_until per day
    by_day = _empty_by_day_compact()
    def _to_minutes(hhmm: Optional[str]) -> Optional[int]:
        if not hhmm: return None
        h, m = map(int, hhmm.split(":"))
        return h*60 + m

    for key in _DAY_KEY:
        opens_candidates = [_to_minutes(s["opens"]) for s in day_slots[key] if s["opens"]]
        closes_candidates = [_to_minutes(s["closes"]) for s in day_slots[key] if s["closes"]]
        food_candidates = [_to_minutes(s["food_until"]) for s in day_slots[key] if s["food_until"]]

        opens_min = min(opens_candidates) if opens_candidates else None
        closes_max = max(closes_candidates) if closes_candidates else None
        food_max = max(food_candidates) if food_candidates else None

        by_day[key]["opens"] = f"{opens_min//60:02d}:{opens_min%60:02d}" if opens_min is not None else None
        by_day[key]["closes"] = f"{closes_max//60:02d}:{closes_max%60:02d}" if closes_max is not None else None
        by_day[key]["food_until"] = f"{food_max//60:02d}:{food_max%60:02d}" if food_max is not None else None

    return {
        "notices_html": notices_html,
        "opening_times": {
            "state": state_text,
            "ranges": ranges,          # original groups preserved
            "by_day": by_day,          # compact per-day with opens/closes/food_until
        },
    }
