## Used chat to help with this integration, ##
# Understanding the documentation for Nominatim #
import json
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

NOMINATIM_BASE = "https://nominatim.openstreetmap.org/search"

_last_call_ts = 0.0


@dataclass
class GeoCandidate:
    display_name: str
    lat: str
    lon: str
    place_id: Optional[int] = None


def _rate_limit_one_per_second():
    global _last_call_ts
    now = time.time()
    elapsed = now - _last_call_ts
    if elapsed < 1.0:
        time.sleep(1.0 - elapsed)
    _last_call_ts = time.time()


def search_city_candidates(query: str, limit: int = 5) -> List[GeoCandidate]:
    """
    Uses Nominatim search API to return a few candidates for a city name.
    """
    query = (query or "").strip()
    if not query:
        return []

    _rate_limit_one_per_second()

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": str(limit),
        "addressdetails": "1",
    }

    # Optional but recommended (docs)
    email = getattr(settings, "NOMINATIM_EMAIL", None)
    if email:
        params["email"] = email

    url = f"{NOMINATIM_BASE}?{urlencode(params)}"

    ua = getattr(settings, "NOMINATIM_USER_AGENT", None)
    if not ua:
        raise ValueError("NOMINATIM_USER_AGENT is not set in settings.py")

    headers = {
        "User-Agent": ua,
        "Accept": "application/json",
    }

    email = getattr(settings, "NOMINATIM_EMAIL", None)
    if email:
        headers["From"] = email

    req = Request(url, headers=headers)

    with urlopen(req, timeout=20) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    results: List[GeoCandidate] = []
    for row in data:
        results.append(
            GeoCandidate(
                display_name=row.get("display_name", ""),
                lat=row.get("lat", ""),
                lon=row.get("lon", ""),
                place_id=row.get("place_id"),
            )
        )
    return results


def geocode_city_best_match(name: str) -> Optional[GeoCandidate]:
    """
    Convenience method to get the top result
    """
    candidates = search_city_candidates(name, limit=1)
    return candidates[0] if candidates else None