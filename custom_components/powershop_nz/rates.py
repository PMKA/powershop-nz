"""Per-band rate helpers (no Home Assistant imports, so they can be unit tested)."""
import re
from typing import Any, Dict, List, Optional

RATE_KEY_PREFIX = "rate_"
_STANDING_KEYWORDS = ("daily", "standing", "fixed", "supply")


def rate_key(label: str) -> str:
    """'Super Off-Peak' -> 'rate_super_off_peak'."""
    slug = re.sub(r"[^a-z0-9]+", "_", (label or "").lower()).strip("_")
    return RATE_KEY_PREFIX + (slug or "unnamed")


def _is_standing(label: str, data: Dict[str, Any]) -> bool:
    category = data.get("band_category")
    if category:
        return category == "STANDING_CHARGE"
    return any(word in label.lower() for word in _STANDING_KEYWORDS)


def consumption_rates(rate_periods: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """Sensor key -> band data for every band except the daily charge (which has its own sensor).

    Keyed by display name rather than the TOU bucket code: codes like "OPK8" look versioned and could
    change on a tariff renewal, which would orphan the sensor's history. Sorted so that any clash
    suffixes stay the same between polls.
    """
    result: Dict[str, Dict[str, Any]] = {}
    for label in sorted(rate_periods):
        data = rate_periods[label]
        if _is_standing(label, data):
            continue
        base = key = rate_key(label)
        n = 2
        while key in result:
            key = f"{base}_{n}"
            n += 1
        result[key] = {**data, "name": label}
    return result


def active_times(tou_schemes: List[Dict[str, Any]], bucket: Optional[str]) -> List[str]:
    """When a band applies, e.g. ["Weekdays 07:00-11:00"]. [] for bands without a TOU bucket."""
    if not bucket:
        return []
    times = []
    for scheme in tou_schemes or []:
        for slot in scheme.get("timeslots") or []:
            if slot.get("timeslot") != bucket:
                continue
            weekdays, weekends = bool(slot.get("weekdays")), bool(slot.get("weekends"))
            # Neither flag set means every day (that's how Night comes back).
            if weekdays and not weekends:
                days = "Weekdays"
            elif weekends and not weekdays:
                days = "Weekends"
            else:
                days = "Every day"
            times.append(f"{days} {(slot.get('activeFrom') or '')[:5]}-{(slot.get('activeTo') or '')[:5]}")
    return times
