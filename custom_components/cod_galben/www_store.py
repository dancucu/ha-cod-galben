"""Persist GIS GeoJSON + Leaflet viewer under Home Assistant www/."""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .api import WarningHit
from .const import WWW_GIS_DIR, WWW_GIS_MAP_HTML
from .gis import geojson_to_svg
from .www_assets import MAP_HTML

_LOGGER = logging.getLogger(__name__)

_MIN_OFFICIAL_SVG_BYTES = 50_000


def www_gis_dir(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("www")) / WWW_GIS_DIR


def official_svg_filename(map_id: str) -> str:
    return f"harta_anm_{map_id}.svg"


def official_svg_local_url(map_id: str) -> str:
    return f"/local/{WWW_GIS_DIR}/{official_svg_filename(map_id)}"


def official_svg_paths(hass: HomeAssistant, map_id: str) -> tuple[Path, Path]:
    """Return (cod_galben path, legacy www/ path)."""
    name = official_svg_filename(map_id)
    www = Path(hass.config.path("www"))
    return www / WWW_GIS_DIR / name, www / name


def official_svg_on_disk(hass: HomeAssistant, map_id: str) -> bool:
    for path in official_svg_paths(hass, map_id):
        try:
            if path.is_file() and path.stat().st_size >= _MIN_OFFICIAL_SVG_BYTES:
                return True
        except OSError:
            continue
    return False


def read_official_svg(hass: HomeAssistant, map_id: str) -> str:
    for path in official_svg_paths(hass, map_id):
        try:
            if path.is_file() and path.stat().st_size >= _MIN_OFFICIAL_SVG_BYTES:
                return path.read_text(encoding="utf-8")
        except OSError:
            continue
    return ""

# Static Leaflet files shipped with the integration
_STATIC_DIR = Path(__file__).parent / "www_static"
_STATIC_FILES = (
    "leaflet.js",
    "leaflet.css",
    "romania.geojson",
    "images/marker-icon.png",
    "images/marker-icon-2x.png",
    "images/marker-shadow.png",
    "images/layers.png",
    "images/layers-2x.png",
)


def _copy_leaflet_assets(target: Path) -> None:
    """Copy vendored Leaflet next to map.html so the iframe needs no CDN."""
    target.mkdir(parents=True, exist_ok=True)
    (target / "images").mkdir(parents=True, exist_ok=True)
    for rel in _STATIC_FILES:
        src = _STATIC_DIR / rel
        if not src.is_file():
            _LOGGER.warning("Missing Leaflet asset: %s", src)
            continue
        dest = target / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
    (target / WWW_GIS_MAP_HTML).write_text(MAP_HTML, encoding="utf-8")


async def async_ensure_gis_assets(hass: HomeAssistant) -> Path:
    """Create www/cod_galben with map.html + Leaflet."""

    def _write() -> Path:
        target = www_gis_dir(hass)
        _copy_leaflet_assets(target)
        return target

    return await hass.async_add_executor_job(_write)


async def async_write_official_svgs(
    hass: HomeAssistant, svg_by_id: dict[str, str]
) -> None:
    """Save official ANM SVG maps for Lovelace <img> (harta_anm_{id}.svg)."""

    def _write() -> None:
        www = Path(hass.config.path("www"))
        target = www_gis_dir(hass)
        target.mkdir(parents=True, exist_ok=True)
        written = 0
        for map_id, text in svg_by_id.items():
            if not map_id or not text:
                continue
            snippet = text.lstrip()[:400].casefold()
            if "<svg" not in snippet:
                continue
            if official_svg_on_disk(hass, map_id):
                continue
            name = official_svg_filename(map_id)
            (target / name).write_text(text, encoding="utf-8")
            # Legacy path used by older Lovelace cards
            (www / name).write_text(text, encoding="utf-8")
            written += 1
        _LOGGER.debug("Wrote %s official ANM SVG map(s)", written)

    await hass.async_add_executor_job(_write)


async def async_write_warning_geojson(
    hass: HomeAssistant, hits: list[WarningHit]
) -> None:
    """Write gis_{map_id}.json (+ .svg fallback) for hits with geojson."""

    def _write() -> None:
        target = www_gis_dir(hass)
        _copy_leaflet_assets(target)
        written = 0
        for hit in hits:
            if not hit.geojson:
                continue
            key = hit.map_id or f"idx_{written}"
            json_path = target / f"gis_{key}.json"
            svg_path = target / f"gis_{key}.svg"
            json_path.write_text(
                json.dumps(hit.geojson, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            # SVG kept as fallback / preview; card uses Leaflet iframe + JSON
            svg_path.write_text(geojson_to_svg(hit.geojson), encoding="utf-8")
            hit.gis_map_path = f"/local/{WWW_GIS_DIR}/gis_{key}.json"
            written += 1
        _LOGGER.debug("Wrote %s GIS map file(s) to %s", written, target)

    await hass.async_add_executor_job(_write)


def clear_geojson_from_summary(block: dict[str, Any]) -> None:
    """Strip accidental geojson keys from summarized warning dicts."""
    for w in block.get("warnings") or []:
        if isinstance(w, dict):
            w.pop("geojson", None)
