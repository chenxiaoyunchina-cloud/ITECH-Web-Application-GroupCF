import json
import re
from dataclasses import dataclass
from typing import Dict, List, Optional
from urllib.parse import quote
from urllib.request import Request, urlopen


WIKIVOYAGE_API = "https://en.wikivoyage.org/w/api.php"


@dataclass
class WikivoyagePlace:
    title: str
    description: str
    lat: float
    long: float
    source_url: str


def _http_get_json(url: str, timeout: int = 20) -> Dict:
    req = Request(url, headers={"User-Agent": "SideQuestCity/1.0 (educational project)"})
    with urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_city_wikitext(city_name: str) -> str:
    """
    Fetch raw wikitext for a city page using the MediaWiki Action API.
    Uses the Revisions API (prop=revisions&rvprop=content). :contentReference[oaicite:1]{index=1}
    """
    title = city_name.replace(" ", "_")
    url = (
        f"{WIKIVOYAGE_API}"
        f"?action=query&format=json&formatversion=2"
        f"&prop=revisions&rvprop=content&rvslots=main"
        f"&titles={quote(title)}"
    )
    data = _http_get_json(url)

    pages = data.get("query", {}).get("pages", [])
    if not pages or "missing" in pages[0]:
        raise ValueError(f"Wikivoyage page not found for city: {city_name}")

    revs = pages[0].get("revisions", [])
    if not revs:
        raise ValueError(f"No revisions found for city: {city_name}")

    slots = revs[0].get("slots", {})
    main = slots.get("main", {})
    content = main.get("content")
    if not isinstance(content, str):
        raise ValueError(f"Unexpected content structure for city: {city_name}")

    return content


def _split_top_level_pipes(template_body: str) -> List[str]:
    parts = []
    buf = []
    brace_depth = 0
    bracket_depth = 0
    i = 0
    while i < len(template_body):
        ch = template_body[i]

        #track nested templates
        if template_body[i:i+2] == "{{":
            brace_depth += 1
            buf.append("{{")
            i += 2
            continue
        if template_body[i:i+2] == "}}":
            brace_depth = max(0, brace_depth - 1)
            buf.append("}}")
            i += 2
            continue

        if template_body[i:i+2] == "[[":
            bracket_depth += 1
            buf.append("[[")
            i += 2
            continue
        if template_body[i:i+2] == "]]":
            bracket_depth = max(0, bracket_depth - 1)
            buf.append("]]")
            i += 2
            continue

        if ch == "|" and brace_depth == 0 and bracket_depth == 0:
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
        i += 1

    parts.append("".join(buf))
    return parts


def _parse_listing_params(raw: str) -> Dict[str, str]:
    tokens = _split_top_level_pipes(raw)
    params: Dict[str, str] = {}
    for t in tokens:
        t = t.strip()
        if not t:
            continue
        if "=" in t:
            k, v = t.split("=", 1)
            params[k.strip().lower()] = v.strip()
        else:
            # unnamed parameter fallback (rare)
            params.setdefault("_unnamed", t.strip())
    return params


def extract_places_from_wikitext(city_name: str, wikitext: str, limit: int = 50) -> List[WikivoyagePlace]:
    page_url = f"https://en.wikivoyage.org/wiki/{quote(city_name.replace(' ', '_'))}"

    # Find templates like {{see|...}}, {{do|...}}, {{listing|...}}
    pattern = re.compile(r"\{\{\s*(see|do|eat|drink|buy|sleep|listing)\s*\|(.*?)\}\}", re.IGNORECASE | re.DOTALL)
    matches = pattern.findall(wikitext)

    places: List[WikivoyagePlace] = []
    for tpl_type, body in matches:
        params = _parse_listing_params(body)

        name = params.get("name") or params.get("_unnamed") or "(Unnamed place)"
        lat_s = params.get("lat")
        long_s = params.get("long")

        if not lat_s or not long_s:
            #skip entries without coordinates (keeps seeding reliable)
            continue

        try:
            lat = float(lat_s)
            lon = float(long_s)
        except ValueError:
            continue

        #use content as short description
        desc = params.get("content") or params.get("alt") or ""
        desc = desc.strip()
        if desc:
            desc = f"[{tpl_type.lower()}] {desc}"
        else:
            desc = f"[{tpl_type.lower()}]"

        places.append(WikivoyagePlace(
            title=name[:120],
            description=desc,
            lat=lat,
            long=lon,
            source_url=page_url,
        ))

        if len(places) >= limit:
            break

    return places