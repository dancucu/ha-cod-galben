"""GIS helpers: ANM coordGis (EPSG:3857 MULTIPOLYGON) → GeoJSON WGS84."""

from __future__ import annotations

import math
import re
from typing import Any
from xml.etree.ElementTree import Element

from .const import ZONE_COLOR_CODES, base_judet_code, county_label

# Web Mercator half-world in meters (EPSG:3857)
_R = 20037508.34

_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")


def mercator_to_wgs84(x: float, y: float) -> list[float]:
    """Convert EPSG:3857 meters to [lon, lat] WGS84."""
    lon = x * 180.0 / _R
    lat = (2.0 * math.atan(math.exp(y * math.pi / _R)) - math.pi / 2.0) * 180.0 / math.pi
    return [lon, lat]


def parse_multipolygon_wkt(wkt: str) -> list[list[list[list[float]]]]:
    """Parse MULTIPOLYGON WKT in EPSG:3857 → MultiPolygon coordinates in WGS84."""
    wkt = (wkt or "").strip()
    if not wkt.upper().startswith("MULTIPOLYGON"):
        return []

    # Extract outermost content after MULTIPOLYGON
    m = re.match(r"MULTIPOLYGON\s*\((.*)\)$", wkt, re.IGNORECASE | re.DOTALL)
    if not m:
        return []
    body = m.group(1)

    polygons: list[str] = []
    depth = 0
    start = 0
    for i, ch in enumerate(body):
        if ch == "(":
            if depth == 0:
                start = i
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                polygons.append(body[start : i + 1])

    out: list[list[list[list[float]]]] = []
    for poly in polygons:
        rings_raw = re.findall(r"\(([^()]+)\)", poly)
        rings: list[list[list[float]]] = []
        for ring in rings_raw:
            nums = [float(x) for x in _NUM_RE.findall(ring)]
            coords: list[list[float]] = []
            for i in range(0, len(nums) - 1, 2):
                coords.append(mercator_to_wgs84(nums[i], nums[i + 1]))
            if len(coords) >= 3:
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                rings.append(coords)
        if rings:
            out.append(rings)
    return out


def build_geojson_for_avertizare(
    avertizare: Element, selected_county: str
) -> dict[str, Any] | None:
    """FeatureCollection for all judet polygons on one ANM message."""
    selected = selected_county.upper()
    features: list[dict[str, Any]] = []

    for judet in avertizare.findall("judet"):
        cod_raw = judet.get("cod") or ""
        cod = base_judet_code(cod_raw)
        if not cod:
            continue
        coords = parse_multipolygon_wkt(judet.get("coordGis") or "")
        if not coords:
            continue
        zone = ZONE_COLOR_CODES.get(judet.get("culoare") or "")
        is_selected = cod == selected
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "cod": cod_raw,
                    "cod_base": cod,
                    "nume": county_label(cod),
                    "culoare": judet.get("culoare"),
                    "culoareNume": zone or "alt",
                    "isSelected": is_selected,
                    "isGalati": is_selected,  # alias for meteo-galati demo style
                },
                "geometry": {
                    "type": "MultiPolygon",
                    "coordinates": coords,
                },
            }
        )

    if not features:
        return None
    return {"type": "FeatureCollection", "features": features}
