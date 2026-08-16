"""Extract ANM mountain/litoral zone overlays from official SVG maps.

The XML feed often lists only county-level colours (e.g. BZ=galben), while
harta.svg.php paints sub-zones (BZ_munte=portocaliu) on top. We parse those
overlays and project them into WGS84 using each county's SVG↔GeoJSON bbox.
"""

from __future__ import annotations

import re
from typing import Any

_ATTR_RE = re.compile(r'([\w:-]+)="([^"]*)"')
_NUM_RE = re.compile(r"-?\d+\.?\d*")
_COD_RE = re.compile(r"\bcod([0-3])\b")

# SVG class codN → same names as ZONE_COLOR_CODES (XML uses 1/2/3; SVG cod0=verde)
_SVG_COD_TO_LEVEL = {
    "0": "informare",  # green on ANM maps — treat as light / non-warning fill
    "1": "galben",
    "2": "portocaliu",
    "3": "rosu",
}

_OVERLAY_HINTS = ("munte", "litoral", "alt400", "alt1400", "alt1500", "alt1600", "alt1700", "depresiune")


def _parse_attrs(tag: str) -> dict[str, str]:
    return {k: v for k, v in _ATTR_RE.findall(tag)}


def _parse_svg_path_points(d: str) -> list[list[float]]:
    """Parse simple ANM path data (M + implicit lineto pairs, optional Z)."""
    if not d:
        return []
    # Tokenize commands and numbers; ANM mostly uses "M x,y x,y ... Z"
    points: list[list[float]] = []
    nums = [float(x) for x in _NUM_RE.findall(d)]
    # After M, coordinates come in pairs
    for i in range(0, len(nums) - 1, 2):
        points.append([nums[i], nums[i + 1]])
    if len(points) >= 3 and points[0] != points[-1]:
        points.append(points[0])
    return points if len(points) >= 4 else []


def _bbox(points: list[list[float]]) -> tuple[float, float, float, float] | None:
    if not points:
        return None
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return min(xs), min(ys), max(xs), max(ys)


def _ring_bbox_geo(ring: list[list[float]]) -> tuple[float, float, float, float] | None:
    if not ring:
        return None
    lons = [p[0] for p in ring]
    lats = [p[1] for p in ring]
    return min(lons), min(lats), max(lons), max(lats)


def _feature_bbox(feat: dict[str, Any]) -> tuple[float, float, float, float] | None:
    geom = feat.get("geometry") or {}
    gtype = geom.get("type")
    coords = geom.get("coordinates") or []
    pts: list[list[float]] = []
    if gtype == "Polygon" and coords:
        pts = coords[0]
    elif gtype == "MultiPolygon":
        for poly in coords:
            if poly:
                pts.extend(poly[0])
    return _ring_bbox_geo(pts)


def _project_point(
    x: float,
    y: float,
    svg_bb: tuple[float, float, float, float],
    geo_bb: tuple[float, float, float, float],
) -> list[float]:
    sx0, sy0, sx1, sy1 = svg_bb
    lon0, lat0, lon1, lat1 = geo_bb
    dx = max(sx1 - sx0, 1e-6)
    dy = max(sy1 - sy0, 1e-6)
    lon = lon0 + (x - sx0) / dx * (lon1 - lon0)
    # SVG y grows downward
    lat = lat1 - (y - sy0) / dy * (lat1 - lat0)
    return [lon, lat]


def _county_svg_bboxes(svg_text: str) -> dict[str, tuple[float, float, float, float]]:
    """BBox of each county outline path (class contains judet)."""
    out: dict[str, tuple[float, float, float, float]] = {}
    for m in re.finditer(r"<path\s([^>]*)/?>", svg_text):
        attrs = _parse_attrs(m.group(1))
        cls = attrs.get("class") or ""
        if not re.search(r"\bjudet\b", cls):
            continue
        if re.search(r"\b(munte|litoral|alt\d+)\b", cls):
            continue
        cod = (attrs.get("data-judet") or "").upper()
        if not cod:
            continue
        pts = _parse_svg_path_points(attrs.get("d") or "")
        bb = _bbox(pts)
        if bb:
            out[cod] = bb
    return out


def extract_visible_overlays(svg_text: str) -> list[dict[str, Any]]:
    """Return mountain/litoral overlays that ANM marks visible (have cod0–3)."""
    overlays: list[dict[str, Any]] = []
    for m in re.finditer(r"<path\s([^>]*)/?>", svg_text):
        attrs = _parse_attrs(m.group(1))
        cls = attrs.get("class") or ""
        if not any(h in cls for h in _OVERLAY_HINTS):
            continue
        cod_m = _COD_RE.search(cls)
        if not cod_m:
            continue  # hidden by default CSS
        level = _SVG_COD_TO_LEVEL.get(cod_m.group(1))
        # Skip green (cod0) — not a warning fill on the official map meaning
        if level in (None, "informare"):
            continue
        county = (attrs.get("data-judet") or "").upper()
        zone = attrs.get("data-munte") or attrs.get("id") or cls
        pts = _parse_svg_path_points(attrs.get("d") or "")
        if len(pts) < 4 or not county:
            continue
        overlays.append(
            {
                "county": county,
                "zone": zone,
                "level": level,
                "svg_cod": cod_m.group(1),
                "points": pts,
            }
        )
    return overlays


def build_county_geojson_from_svg(
    svg_text: str,
    selected_county: str | None = None,
    *,
    default_level: str = "informare",
) -> dict[str, Any] | None:
    """Build county FeatureCollection from ANM SVG when XML has no coordGis.

    Projects path coordinates using the SVG viewBox onto a fixed Romania WGS84
    bbox (same framing as geojson_to_svg). Used for national informare messages
    that list no <judet> polygons.
    """
    if not svg_text:
        return None

    vb = re.search(r'viewBox="([^"]+)"', svg_text)
    if not vb:
        return None
    try:
        vx0, vy0, vw, vh = (float(x) for x in vb.group(1).split())
    except ValueError:
        return None
    if vw <= 0 or vh <= 0:
        return None

    # Match geojson_to_svg / Leaflet ROMANIA bounds
    min_lon, max_lon = 20.15, 29.75
    min_lat, max_lat = 43.55, 48.30
    selected = (selected_county or "").upper()
    features: list[dict[str, Any]] = []
    seen: set[str] = set()

    for m in re.finditer(r"<path\s([^>]*)/?>", svg_text):
        attrs = _parse_attrs(m.group(1))
        cls = attrs.get("class") or ""
        if not re.search(r"\bjudet\b", cls):
            continue
        if re.search(r"\b(munte|litoral|alt\d+|depresiune)\b", cls):
            continue
        cod = (attrs.get("data-judet") or "").upper().split("_", 1)[0]
        if not cod or cod in seen:
            continue
        cod_m = _COD_RE.search(cls)
        if cod_m:
            level = _SVG_COD_TO_LEVEL.get(cod_m.group(1), default_level)
        else:
            # Informare maps often omit codN on every county — still paint them
            level = default_level
        pts = _parse_svg_path_points(attrs.get("d") or "")
        if len(pts) < 4:
            continue
        ring = [
            [
                min_lon + (x - vx0) / vw * (max_lon - min_lon),
                max_lat - (y - vy0) / vh * (max_lat - min_lat),
            ]
            for x, y in pts
        ]
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        seen.add(cod)
        is_selected = cod == selected
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "cod": cod,
                    "cod_base": cod,
                    "nume": cod,
                    "culoare": cod_m.group(1) if cod_m else "0",
                    "culoareNume": level,
                    "isSelected": is_selected,
                    "isGalati": is_selected,
                    "fromSvg": True,
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )

    if not features:
        return None
    return {"type": "FeatureCollection", "features": features}


def merge_svg_overlays_into_geojson(
    geojson: dict[str, Any], svg_text: str, selected_county: str | None = None
) -> dict[str, Any]:
    """Append projected mountain overlays onto a county FeatureCollection."""
    if not geojson or not svg_text:
        return geojson

    features = list(geojson.get("features") or [])
    by_county: dict[str, dict[str, Any]] = {}
    for feat in features:
        props = feat.get("properties") or {}
        base = (props.get("cod_base") or props.get("cod") or "").upper()
        base = base.split("_", 1)[0]
        if base and base not in by_county:
            by_county[base] = feat

    svg_bbs = _county_svg_bboxes(svg_text)
    selected = (selected_county or "").upper()
    added = 0

    for ov in extract_visible_overlays(svg_text):
        county = ov["county"]
        feat = by_county.get(county)
        if not feat:
            continue
        geo_bb = _feature_bbox(feat)
        svg_bb = svg_bbs.get(county)
        if not geo_bb or not svg_bb:
            continue
        ring = [_project_point(x, y, svg_bb, geo_bb) for x, y in ov["points"]]
        if len(ring) < 4:
            continue
        is_selected = county == selected
        features.append(
            {
                "type": "Feature",
                "properties": {
                    "cod": ov["zone"],
                    "cod_base": county,
                    "nume": f"{county} (zonă)",
                    "culoare": ov["svg_cod"],
                    "culoareNume": ov["level"],
                    "isSelected": is_selected,
                    "isGalati": is_selected,
                    "zoneType": "overlay",
                    "overlay": True,
                },
                "geometry": {"type": "Polygon", "coordinates": [ring]},
            }
        )
        added += 1

    if added:
        # Base counties first, overlays on top; selected last among peers
        def sort_key(f: dict[str, Any]) -> tuple[int, int]:
            p = f.get("properties") or {}
            overlay = 1 if p.get("overlay") else 0
            sel = 1 if p.get("isSelected") else 0
            return (overlay, sel)

        features.sort(key=sort_key)

    return {"type": "FeatureCollection", "features": features}
