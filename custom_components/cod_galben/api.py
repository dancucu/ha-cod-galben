"""XML parsers for ANM avertizări and nowcasting feeds."""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime
from html import unescape
from typing import Any
from xml.etree import ElementTree as ET

from homeassistant.util import dt as dt_util

from .const import (
    LEVEL_GALBEN,
    LEVEL_INFORMARE,
    LEVEL_NONE,
    OVERALL_COLOR_CODES,
    URL_HARTA_SVG,
    ZONE_COLOR_CODES,
    base_judet_code,
    max_level,
    normalize_county_token,
)
from .gis import build_geojson_for_avertizare

_LOGGER = logging.getLogger(__name__)

_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_JUDET_RE = re.compile(
    r"jude[tț]ul?\s+([A-Za-zăâîșțĂÂÎȘȚ\- ]+?)(?:\s*:|\s*;|,|$)",
    re.IGNORECASE,
)


@dataclass
class WarningHit:
    """A single warning relevant to the selected county."""

    source: str  # avertizare | nowcasting
    level: str
    tip: str
    fenomene: str
    start: str | None
    end: str | None
    interval_text: str
    zona: str
    judet_codes: list[str]
    mesaj: str
    message_excerpt: str  # short preview (kept for older Lovelace cards)
    map_id: str | None = None  # ANM harta.svg.php?id_avertizare=
    map_url: str | None = None
    gis_map_path: str | None = None  # /local/cod_galben/gis_{id}.json
    # Full GeoJSON kept in memory for writing to www — never published to HA state
    geojson: dict[str, Any] | None = field(default=None, repr=False)

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data.pop("geojson", None)
        return data


_MAP_ID_RE = re.compile(r"id_avertizare=(\d+)")
_MESAJ_NUM_RE = re.compile(r"MESAJ\s+(\d+)\s*/\s*\d+", re.IGNORECASE)


def extract_map_ids_from_html(html: str) -> list[str]:
    """Ordered unique map IDs from the ANM avertizări HTML page."""
    seen: set[str] = set()
    out: list[str] = []
    for mid in _MAP_ID_RE.findall(html or ""):
        if mid not in seen:
            seen.add(mid)
            out.append(mid)
    return out


def assign_map_ids(hits: list[WarningHit], map_ids: list[str]) -> None:
    """Attach map_id/map_url to hits using MESAJ N/M index into national map list."""
    if not map_ids:
        return

    for hit in hits:
        if hit.source != "avertizare":
            continue
        m = _MESAJ_NUM_RE.search(hit.message_excerpt or "")
        if not m:
            continue
        idx = int(m.group(1)) - 1
        if 0 <= idx < len(map_ids):
            hit.map_id = map_ids[idx]
            hit.map_url = URL_HARTA_SVG.format(id=hit.map_id)
            hit.gis_map_path = f"/local/cod_galben/gis_{hit.map_id}.svg"


def _strip_html(raw: str) -> str:
    text = unescape(raw or "")
    text = _TAG_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _parse_anm_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S", "%d-%m-%Y %H:%M"):
        try:
            naive = datetime.strptime(value, fmt)
            return dt_util.as_local(naive.replace(tzinfo=None))
        except ValueError:
            continue
    try:
        parsed = dt_util.parse_datetime(value)
        if parsed:
            return dt_util.as_local(parsed)
    except (TypeError, ValueError):
        pass
    return None


def _iso(dt: datetime | None) -> str | None:
    return dt.isoformat() if dt else None


def _extract_fenomene_from_mesaj(mesaj: str) -> str:
    text = _strip_html(mesaj)
    m = re.search(r"Fenomene vizate:\s*([^Z]+?)(?:Zone afectate:|$)", text, re.I)
    if m:
        return m.group(1).strip(" .-")
    return ""


def _extract_interval_from_mesaj(mesaj: str) -> str:
    text = _strip_html(mesaj)
    m = re.search(r"Interval de valabilitate:\s*([^F]+?)(?:Fenomene|$)", text, re.I)
    if m:
        return m.group(1).strip(" .-")
    return ""


_DAY_OR_NARRATIVE_RE = re.compile(
    r"("
    r"(?:Luni|Marți|Marti|Miercuri|Joi|Vineri|Sâmbătă|Sambata|Duminică|Duminica"
    r"|În\s+noaptea|In\s+noaptea|În\s+intervalul|In\s+intervalul"
    r"|Pe\s+parcursul|Astăzi|Astazi|Mâine|Maine)"
    r".+"
    r")",
    re.IGNORECASE | re.DOTALL,
)


def _extract_descriere_from_mesaj(mesaj: str) -> str:
    """Narrative body (temps, precip amounts) after ANM structured headers."""
    text = _strip_html(mesaj)
    if not text:
        return ""

    after_zone = re.search(
        r"Zone afectate:\s*(?:conform textului și hărții\s*)?(.*)$",
        text,
        re.IGNORECASE | re.DOTALL,
    )
    body = after_zone.group(1).strip(" .-") if after_zone else text

    day = _DAY_OR_NARRATIVE_RE.search(body)
    if day:
        return _SPACE_RE.sub(" ", day.group(1)).strip()
    return _SPACE_RE.sub(" ", body).strip()


def _is_informare(tip_mesaj: str, nume_tip: str, nume_culoare: str) -> bool:
    blob = f"{tip_mesaj} {nume_tip} {nume_culoare}".casefold()
    return "informare" in blob


def _zone_level(culoare: str | None) -> str | None:
    if culoare is None:
        return None
    return ZONE_COLOR_CODES.get(culoare)


def _overall_level(culoare: str | None, nume_culoare: str | None) -> str:
    if nume_culoare:
        name = unescape(nume_culoare).casefold().strip()
        if name in ("galben", "portocaliu", "rosu", "roșu"):
            return "rosu" if name.startswith("ro") else name
        if "informare" in name or name in ("gri", "gray", "grey"):
            return LEVEL_INFORMARE
    if culoare is not None and culoare in OVERALL_COLOR_CODES:
        return OVERALL_COLOR_CODES[culoare]
    return LEVEL_NONE


def _county_matches_zone(cod: str, county: str) -> bool:
    return base_judet_code(cod) == county.upper()


def extract_counties_from_zona(zona: str) -> list[str]:
    """Extract ANM county codes mentioned in a nowcasting zona string."""
    zona = unescape(zona or "")
    found: list[str] = []
    seen: set[str] = set()

    for match in _JUDET_RE.finditer(zona):
        code = normalize_county_token(match.group(1))
        if code and code not in seen:
            seen.add(code)
            found.append(code)

    # fallback: look for known county names anywhere in text
    if not found:
        lower = zona.casefold()
        from .const import JUDETE

        for code, name in JUDETE.items():
            if name.casefold() in lower or f" {code.casefold()} " in f" {lower} ":
                if code not in seen:
                    seen.add(code)
                    found.append(code)

    return found


def parse_avertizari_xml(xml_text: str, county: str) -> list[WarningHit]:
    """Parse general warnings XML and return hits for county."""
    hits: list[WarningHit] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as err:
        _LOGGER.error("Invalid avertizari XML: %s", err)
        return hits

    county = county.upper()
    for av in root.findall(".//avertizare"):
        tip = unescape(av.get("numeTipMesaj") or "")
        tip_mesaj = av.get("tipMesaj") or ""
        nume_culoare = av.get("numeCuloare") or ""
        mesaj = av.get("mesaj") or ""
        fenomene_attr = unescape(av.get("fenomeneVizate") or "")
        fenomene = _extract_fenomene_from_mesaj(mesaj) or fenomene_attr
        if fenomene.casefold() in ("conform textului",):
            fenomene = _extract_fenomene_from_mesaj(mesaj) or fenomene
        interval_text = _extract_interval_from_mesaj(mesaj) or unescape(
            av.get("intervalul") or ""
        )
        start = _parse_anm_dt(av.get("dataAparitiei"))
        end = _parse_anm_dt(av.get("dataExpirarii"))
        mesaj_text = _strip_html(mesaj)
        descriere = _extract_descriere_from_mesaj(mesaj) or mesaj_text
        excerpt = mesaj_text[:280]

        informare = _is_informare(tip_mesaj, tip, nume_culoare)
        judete = list(av.findall("judet"))
        geojson = build_geojson_for_avertizare(av, county)

        if informare:
            # Informare: usually national — treat selected county as affected
            codes = sorted(
                {
                    base_judet_code(j.get("cod") or "")
                    for j in judete
                    if j.get("cod")
                }
            )
            hits.append(
                WarningHit(
                    source="avertizare",
                    level=LEVEL_INFORMARE,
                    tip=tip or "Informare meteorologică",
                    fenomene=fenomene or "Informare meteorologică",
                    start=_iso(start),
                    end=_iso(end),
                    interval_text=interval_text,
                    zona=unescape(av.get("zonaAfectata") or "întreg teritoriul"),
                    judet_codes=codes or [county],
                    mesaj=descriere,
                    message_excerpt=excerpt,
                    geojson=geojson,
                )
            )
            continue

        # Prefer zone colour for this county (handles mixed yellow/orange maps)
        matching_zones = [
            j for j in judete if _county_matches_zone(j.get("cod") or "", county)
        ]
        if not matching_zones:
            continue

        zone_levels = [
            lvl
            for j in matching_zones
            if (lvl := _zone_level(j.get("culoare"))) is not None
        ]

        if zone_levels:
            level = max_level(zone_levels)
        else:
            # Pure map / missing zone colour — fall back to overall
            level = _overall_level(av.get("culoare"), nume_culoare)

        if level in (LEVEL_NONE,):
            continue

        hits.append(
            WarningHit(
                source="avertizare",
                level=level,
                tip=tip or "Avertizare meteorologică",
                fenomene=fenomene or "conform mesajului ANM",
                start=_iso(start),
                end=_iso(end),
                interval_text=interval_text,
                zona=unescape(av.get("zonaAfectata") or ""),
                judet_codes=[county],
                mesaj=descriere,
                message_excerpt=excerpt,
                geojson=geojson,
            )
        )

    return hits


def parse_nowcasting_xml(xml_text: str, county: str) -> list[WarningHit]:
    """Parse nowcasting XML (attribute form and optional judet GIS children)."""
    hits: list[WarningHit] = []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as err:
        _LOGGER.error("Invalid nowcasting XML: %s", err)
        return hits

    county = county.upper()
    # Root may be <avertizariNowcasting> or a single <avertizare>
    elements = root.findall(".//avertizare")
    if root.tag == "avertizare" and not elements:
        elements = [root]

    for av in elements:
        tip = unescape(av.get("numeTipMesaj") or av.get("tipMesaj") or "Nowcasting")
        tip_code = av.get("tipMesaj") or ""
        nume_culoare = av.get("numeCuloare") or ""
        zona = unescape(av.get("zona") or "")
        semnalare = unescape(av.get("semnalare") or "")
        fenomene = semnalare or unescape(av.get("fenomeneVizate") or "")

        start = _parse_anm_dt(
            av.get("dataInceput") or av.get("dataAparitiei")
        )
        end = _parse_anm_dt(av.get("dataSfarsit") or av.get("dataExpirarii"))

        informare = _is_informare(tip_code, tip, nume_culoare)

        judete = list(av.findall("judet"))
        matched = False
        level = LEVEL_NONE
        codes: list[str] = []

        if judete:
            matching = [
                j for j in judete if _county_matches_zone(j.get("cod") or "", county)
            ]
            if matching:
                matched = True
                zone_levels = [
                    lvl
                    for j in matching
                    if (lvl := _zone_level(j.get("culoare"))) is not None
                ]
                level = (
                    max_level(zone_levels)
                    if zone_levels
                    else _overall_level(av.get("culoare"), nume_culoare)
                )
                codes = [county]
        else:
            codes = extract_counties_from_zona(zona)
            if county in codes or informare:
                matched = True
                level = (
                    LEVEL_INFORMARE
                    if informare
                    else _overall_level(av.get("culoare"), nume_culoare)
                )

        if not matched or level == LEVEL_NONE:
            continue

        interval_text = ""
        if start and end:
            interval_text = f"{start.strftime('%d.%m.%Y %H:%M')} – {end.strftime('%d.%m.%Y %H:%M')}"

        fenomene_text = _strip_html(fenomene)
        hits.append(
            WarningHit(
                source="nowcasting",
                level=level,
                tip=tip,
                fenomene=fenomene or "Nowcasting",
                start=_iso(start),
                end=_iso(end),
                interval_text=interval_text,
                zona=zona,
                judet_codes=codes or [county],
                mesaj=fenomene_text,
                message_excerpt=fenomene_text[:280],
            )
        )

    return hits


def summarize_hits(hits: list[WarningHit]) -> dict[str, Any]:
    """Build coordinator summary for a list of hits."""
    if not hits:
        return {
            "afectat": False,
            "nivel": LEVEL_NONE,
            "fenomene": "Nicio avertizare",
            "valabil_de": None,
            "valabil_pana": None,
            "interval": None,
            "tip": None,
            "mesaj": None,
            "count": 0,
            "map_ids": [],
            "warnings": [],
        }

    nivel = max_level([h.level for h in hits])
    primary = next((h for h in hits if h.level == nivel), hits[0])
    fenomene_parts = []
    for h in hits:
        if h.fenomene and h.fenomene not in fenomene_parts:
            fenomene_parts.append(h.fenomene)

    map_ids = [h.map_id for h in hits if h.map_id]
    return {
        "afectat": True,
        "nivel": nivel,
        "fenomene": "; ".join(fenomene_parts) if fenomene_parts else primary.fenomene,
        "valabil_de": primary.start,
        "valabil_pana": primary.end,
        "interval": primary.interval_text or None,
        "tip": primary.tip,
        "mesaj": primary.mesaj or None,
        "count": len(hits),
        "map_ids": map_ids,
        "warnings": [h.as_dict() for h in hits],
    }
