import dateparser
from bs4 import BeautifulSoup
from typing import Any, Dict, List, Optional

def _clean_text(s: str | None) -> str:
    if not s:
        return ""
    return " ".join(s.split()).strip()


def _conv_price(v: Optional[str]) -> Optional[float]:
    if v is None:
        return None
    v = v.replace(".", "").replace(",", ".")
    try:
        return float(v)
    except ValueError:
        return None


def _parse_price_attrs(el) -> Dict[str, Optional[float]]:
    if not el:
        return {"student": None, "servant": None, "guest": None}
    return {
        "student": _conv_price(el.get("data-price-student")),
        "servant": _conv_price(el.get("data-price-servant")),
        "guest": _conv_price(el.get("data-price-guest")),
    }


def _parse_co2(additives_block) -> Optional[int]:
    if not additives_block:
        return None
    co2 = additives_block.select_one(".co2-per-serving span")
    if not co2:
        return None
    raw = _clean_text(co2.get_text())
    if raw.lower().startswith("kein"):
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    return int(digits) if digits.isdigit() else None


def _parse_allergens(additives_block) -> List[str]:
    if not additives_block:
        return []
    out: List[str] = []
    for li in additives_block.select("ul li"):
        t = _clean_text(li.get_text())
        if t:
            out.append(t)
    return out


def _food_tags(icon_container) -> List[str]:
    tags: List[str] = []
    if not icon_container:
        return tags
    for sp in icon_container.select("span.food-icon"):
        t = _clean_text(sp.get("data-type-title") or "")
        if t:
            tags.append(t)
            continue
        classes = [c for c in (sp.get("class") or []) if c != "food-icon"]
        if classes:
            tags.append(classes[-1])
    return tags


def _parse_date_label(label: Optional[str]) -> Optional[str]:
    """
    Parse a German date label into ISO format (YYYY-MM-DD).
    Discards any leading words until the first digit (day of month).
    Examples:
        "Heute, 1. September 2025" -> "2025-09-01"
        "Morgen, 2. September 2025" -> "2025-09-02"
        "Montag, 1. September 2025" -> "2025-09-01"
        "01.09.2025" -> "2025-09-01"
    """
    if not label:
        return None

    s = label.strip()

    # cut away everything before the first digit
    for i, ch in enumerate(s):
        if ch.isdigit():
            s = s[i:]
            break

    dt = dateparser.parse(s, languages=["de"])
    if not dt:
        return None
    return dt.date().isoformat()


def parse_html_menu(html: str) -> Dict[str, Any]:
    soup = BeautifulSoup(html, "html.parser")
    root = soup.select_one(".gastronomy")
    if not root:
        return {"notices": [], "opening_times": {}, "weeks": [], "trimmings": [], "legend": {}}

    # --- Notices (collect all) ---
    # NOTE: per request, this parsing is disabled. Keeping code commented for reference.
    # notices: List[str] = []
    # for n in root.select(".notice.notice_menu"):
    #     text = " ".join(_clean_text(p.get_text()) for p in n.select("p")) or _clean_text(n.get_text())
    #     text = _clean_text(text)
    #     if text:
    #         notices.append(text)
    notices: List[str] = []

    # --- Opening times (today + ranges) ---
    # NOTE: per request, this parsing is disabled. Keeping code commented for reference.
    # def extract_opening_time_blocks(scope) -> List[Dict[str, str]]:
    #     blocks: List[Dict[str, str]] = []
    #     if not scope:
    #         return blocks
    #     for ot in scope.select(".opening-time"):
    #         time_el = ot.select_one(".opening-times__time")
    #         meta_el = ot.select_one(".opening-times__meta")
    #         blocks.append({
    #             "time": _clean_text(time_el.get_text()) if time_el else "",
    #             "meta": _clean_text(meta_el.get_text()) if meta_el else "",
    #         })
    #     return blocks
    #
    # opening = root.select_one(".opening-times_menu")
    # opening_state = _clean_text(opening.select_one(".opening-time_state").get_text()) if opening else None
    # today_blocks = extract_opening_time_blocks(opening.select_one(".opening-time_listing")) if opening else []
    #
    # all_ranges: List[Dict[str, str]] = []
    # if opening:
    #     for rng in opening.select(".opening-time_listing-all .opening-time_days"):
    #         day_range = _clean_text((rng.select_one(".opening-time-day-range") or rng).get_text())
    #         sets = extract_opening_time_blocks(rng.select_one(".opening-time_set"))
    #         if sets:
    #             for ot in sets:
    #                 all_ranges.append({"days": day_range, "time": ot["time"], "meta": ot["meta"]})
    #         else:
    #             all_ranges.append({"days": day_range, "time": "", "meta": ""})

    # For closed detection, we need a simplified flag only
    opening_state = None
    today_blocks: List[Dict[str, str]] = []
    all_ranges: List[Dict[str, str]] = []

    # helper: detect if a .day-menu explicitly says there are no meals
    def _day_has_no_meals_notice(day_el) -> bool:
        msg_el = day_el.select_one(".day-menu-entries .notice")
        if not msg_el:
            return False
        txt = msg_el.get_text(" ", strip=True).casefold()
        triggers = [
            "aktuell keine daten",
            "keine daten vorhanden",
            "heute geschlossen",
            "geschlossen",
            "keine ausgabe",
            "kein angebot",
        ]
        return any(t in txt for t in triggers)

    is_globally_closed = (opening_state or "").casefold().find("geschlossen") >= 0

    # --- Weeks & days ---
    weeks: List[Dict[str, Any]] = []
    for w in root.select(".week-menu"):
        week_no = w.get("data-week")
        days: List[Dict[str, Any]] = []

        for day in w.select(":scope > .day-menu"):
            day_id = day.get("data-day")
            date_h = day.select_one("h3")
            date_label = _clean_text(date_h.get_text()) if date_h else None
            # NEW: derive ISO date
            date_iso = _parse_date_label(date_label)

            entries: List[Dict[str, Any]] = []
            for art in day.select(".day-menu-entries > article"):
                main = art.select_one(".menu-entry_main-row")
                if not main:
                    continue

                title_el = main.find("h5")
                title = _clean_text(title_el.get_text()) if title_el else ""
                price_el = main.select_one(".price")
                prices = _parse_price_attrs(price_el)
                icons = main.select_one(".food-type")
                tags = _food_tags(icons)

                add_row = art.select_one(".menu-entry_additives-row")
                climate = bool(add_row and add_row.select_one(".climate-plate"))
                add_block = add_row.select_one(".additives .additive-list") if add_row else None
                co2 = _parse_co2(add_block)
                allergens = _parse_allergens(add_block)

                entries.append({
                    "id": art.get("data-dispo"),
                    "title": title,
                    "tags": tags,
                    "prices": prices,
                    "co2_g": co2,
                    "allergens": allergens,
                    "climate_plate": climate,
                })

            # NEW: decide closed-ness
            day_is_closed = (len(entries) == 0 and (_day_has_no_meals_notice(day) or is_globally_closed))

            days.append({
                "day_id": day_id,
                "date_label": date_label,
                "date_iso": date_iso,  # NEW field in yyyy-mm-dd
                "entries": entries,
                "is_closed": day_is_closed,
            })

        weeks.append({"week": week_no, "days": days})

    # --- Trimmings ---
    trimmings: List[Dict[str, Any]] = []
    for t in root.select(".trimming-entries .menu-entry_main-row"):
        name_el = t.select_one("h5.name")
        price_el = t.select_one(".price")
        if name_el and price_el:
            trimmings.append({
                "name": _clean_text(name_el.get_text()),
                "prices": _parse_price_attrs(price_el),
            })

    # --- Legend ---
    legend_map: Dict[str, str] = {}
    legend = root.select_one(".legend.food-type")
    if legend:
        for li in legend.select("li"):
            sp = li.select_one("span.food-icon")
            label = _clean_text(li.get_text())
            if not sp or not label:
                continue
            cls = [c for c in sp.get("class", []) if c != "food-icon"]
            if cls:
                legend_map[cls[-1]] = label

    return {
        "notices": notices,
        "opening_times": {
            "state": opening_state,
            "today": today_blocks,
            "ranges": all_ranges,
        },
        "weeks": weeks,
        "trimmings": trimmings,
        "legend": legend_map,
    }
