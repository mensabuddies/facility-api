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

    # split on common separators first: commas, 'und', slashes, semicolons
    parts = re.split(r"\s*(?:,|und|/|;)\s*", text)

    idxs: List[int] = []
    for part in parts:
        # ranges: "-", "–", "bis"
        m = re.split(r"\s*(?:-|–|bis)\s*", part)
        if len(m) == 1:
            d = _norm_day_token(m[0])
            if d is not None:
                idxs.append(_DAY_ORDER.index(d))
        elif len(m) == 2:
            a, b = _norm_day_token(m[0]), _norm_day_token(m[1])
            if a is None or b is None:
                continue
            ia, ib = _DAY_ORDER.index(a), _DAY_ORDER.index(b)
            if ia <= ib:
                idxs.extend(range(ia, ib + 1))
            else:
                # unlikely, but if someone writes "Freitag - Montag", cover wrap
                idxs.extend(list(range(ia, 7)) + list(range(0, ib + 1)))
    # de-dup while preserving order
    seen = set()
    out: List[int] = []
    for i in idxs:
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out

def _empty_by_day() -> Dict[str, List[Dict[str, str]]]:
    return {k: [] for k in _DAY_KEY}

def _state_text_without_icon(state_el) -> Optional[str]:
    if not state_el:
        return None
    # clone then drop icons to avoid "schedule " prefix
    for sp in state_el.select(".icon-mi, .icon-mi-filled"):
        sp.extract()
    return _clean_text(state_el.get_text())

# --- main parser --------------------------------------------------------------

def parse_html_detail(html: str) -> Dict[str, Any]:
    """
    Detail page → notices (HTML), opening times by ranges AND by individual weekday.
    """
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".gastronomy")
    if not root:
        return {"notices_html": [], "opening_times": {"state": None, "ranges": [], "by_day": _empty_by_day()}}

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

    # --- NEW: expand ranges into by_day mapping
    by_day = _empty_by_day()
    for r in ranges:
        day_idxs = _expand_days(r["days"])
        for di in day_idxs:
            key = _DAY_KEY[di]  # e.g., "monday"
            # append copies so consumers can mutate safely
            for slot in r["times"] or []:
                by_day[key].append({"time": slot["time"], "meta": slot["meta"]})
            # even if no explicit times for that range, keep empty list => no entry appended

    return {
        "notices_html": notices_html,
        "opening_times": {
            "state": state_text,
            "ranges": ranges,   # original groups
            "by_day": by_day,   # normalized per weekday
        },
    }
