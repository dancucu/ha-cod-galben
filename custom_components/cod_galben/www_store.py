"""Persist GIS GeoJSON + Leaflet viewer under Home Assistant www/."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from homeassistant.core import HomeAssistant

from .api import WarningHit
from .const import WWW_GIS_DIR, WWW_GIS_MAP_HTML
from .www_assets import MAP_HTML

_LOGGER = logging.getLogger(__name__)


def www_gis_dir(hass: HomeAssistant) -> Path:
    return Path(hass.config.path("www")) / WWW_GIS_DIR


async def async_ensure_gis_assets(hass: HomeAssistant) -> Path:
    """Create www/cod_galben and write map.html viewer."""

    def _write() -> Path:
        target = www_gis_dir(hass)
        target.mkdir(parents=True, exist_ok=True)
        map_path = target / WWW_GIS_MAP_HTML
        map_path.write_text(MAP_HTML, encoding="utf-8")
        return target

    return await hass.async_add_executor_job(_write)


async def async_write_warning_geojson(
    hass: HomeAssistant, hits: list[WarningHit]
) -> None:
    """Write gis_{map_id}.json for hits that have geojson + map_id."""

    def _write() -> None:
        target = www_gis_dir(hass)
        target.mkdir(parents=True, exist_ok=True)
        written = 0
        for hit in hits:
            if not hit.geojson:
                continue
            key = hit.map_id or f"idx_{written}"
            path = target / f"gis_{key}.json"
            path.write_text(
                json.dumps(hit.geojson, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            hit.gis_map_path = f"/local/{WWW_GIS_DIR}/gis_{key}.json"
            written += 1
        _LOGGER.debug("Wrote %s GIS geojson file(s) to %s", written, target)

    await hass.async_add_executor_job(_write)


def clear_geojson_from_summary(block: dict[str, Any]) -> None:
    """Strip accidental geojson keys from summarized warning dicts."""
    for w in block.get("warnings") or []:
        if isinstance(w, dict):
            w.pop("geojson", None)
