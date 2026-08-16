"""GIS helpers: ANM coordGis (EPSG:3857 MULTIPOLYGON) → GeoJSON WGS84 + SVG."""

from __future__ import annotations

import math
import re
from typing import Any
from xml.etree.ElementTree import Element

from .const import ZONE_COLOR_CODES, base_judet_code, county_label

# Web Mercator half-world in meters (EPSG:3857)
_R = 20037508.34

_NUM_RE = re.compile(r"[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?")

_FILL = {
    "galben": "#fdd835",
    "portocaliu": "#fb8c00",
    "rosu": "#e53935",
    "informare": "#9e9e9e",
    "alt": "#9e9e9e",
}
_EDGE = {
    "galben": "#f9a825",
    "portocaliu": "#ef6c00",
    "rosu": "#b71c1c",
    "informare": "#757575",
    "alt": "#757575",
}


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
                    "isGalati": is_selected,
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


def _iter_rings(geometry: dict[str, Any]) -> list[list[list[float]]]:
    gtype = geometry.get("type")
    coords = geometry.get("coordinates") or []
    if gtype == "Polygon":
        return coords  # list of rings
    if gtype == "MultiPolygon":
        rings: list[list[list[float]]] = []
        for poly in coords:
            rings.extend(poly)
        return rings
    return []


def geojson_to_svg(
    geojson: dict[str, Any], *, width: int = 720, height: int = 480, pad: float = 12.0
) -> str:
    """Render FeatureCollection to SVG on a full-Romania white canvas (fallback)."""
    # Fixed Romania bbox (lon/lat) — same framing as official ANM map
    min_lon, max_lon = 20.15, 29.75
    min_lat, max_lat = 43.55, 48.30
    features = geojson.get("features") or []
    prepared: list[tuple[dict[str, Any], list[list[list[float]]]]] = []

    for feat in features:
        geom = feat.get("geometry") or {}
        rings = _iter_rings(geom)
        if not rings:
            continue
        prepared.append((feat.get("properties") or {}, rings))

    span_lon = max_lon - min_lon
    span_lat = max_lat - min_lat
    usable_w = width - 2 * pad
    usable_h = height - 2 * pad
    scale = min(usable_w / span_lon, usable_h / span_lat)

    def project(lon: float, lat: float) -> tuple[float, float]:
        x = pad + (lon - min_lon) * scale + (usable_w - span_lon * scale) / 2
        y = pad + (max_lat - lat) * scale + (usable_h - span_lat * scale) / 2
        return x, y

    prepared.sort(
        key=lambda item: bool(item[0].get("isSelected") or item[0].get("isGalati"))
    )

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}" role="img">',
        '<rect width="100%" height="100%" fill="#ffffff"/>',
    ]

    for props, rings in prepared:
        name = props.get("culoareNume") or "alt"
        selected = bool(props.get("isSelected") or props.get("isGalati"))
        fill = _FILL.get(name, _FILL["alt"])
        stroke = "#bf360c" if selected else "#333333"
        stroke_w = 2.2 if selected else 0.5
        opacity = 0.85 if selected else 0.55
        for ring in rings:
            if len(ring) < 3:
                continue
            pts = " ".join(
                f"{project(lon, lat)[0]:.2f},{project(lon, lat)[1]:.2f}"
                for lon, lat in ring
            )
            parts.append(
                f'<polygon points="{pts}" fill="{fill}" fill-opacity="{opacity}" '
                f'stroke="{stroke}" stroke-width="{stroke_w}" stroke-linejoin="round"/>'
            )
        # one label per județ (centroid of outer ring)
        if rings and rings[0] and len(rings[0]) >= 3:
            ring0 = rings[0]
            xs = [project(lon, lat)[0] for lon, lat in ring0]
            ys = [project(lon, lat)[1] for lon, lat in ring0]
            cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
            code = props.get("cod_base") or str(props.get("cod") or "").split("_")[0]
            if code:
                parts.append(
                    f'<text x="{cx:.1f}" y="{cy:.1f}" text-anchor="middle" '
                    f'dominant-baseline="middle" font-size="9" '
                    f'font-family="system-ui,sans-serif" fill="#222" '
                    f'font-weight="600">{code}</text>'
                )

    parts.append("</svg>")
    return "".join(parts)
