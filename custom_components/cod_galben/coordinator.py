"""DataUpdateCoordinator for Cod Galben."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    assign_map_ids,
    extract_map_ids_from_html,
    parse_avertizari_xml,
    parse_nowcasting_xml,
    summarize_hits,
)
from .const import (
    CONF_COUNTY,
    CONF_GIS_BASEMAP,
    CONF_MAP_STYLE,
    DOMAIN,
    GIS_BASEMAP_DEFAULT,
    MAP_STYLE_DEFAULT,
    UPDATE_INTERVAL_SECONDS,
    URL_AVERTIZARI,
    URL_AVERTIZARI_PAGE,
    URL_HARTA_SVG,
    URL_NOWCASTING,
    URL_NOWCASTING_GIS,
    county_label,
)
from .svg_overlays import merge_svg_overlays_into_geojson
from .www_store import (
    async_ensure_gis_assets,
    async_write_warning_geojson,
    clear_geojson_from_summary,
)

_LOGGER = logging.getLogger(__name__)


class CodGalbenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and parse ANM warnings for one county."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.entry = entry
        self.county = entry.data[CONF_COUNTY].upper()
        self.county_name = county_label(self.county)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.county}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

    @property
    def map_style(self) -> str:
        return self.entry.options.get(CONF_MAP_STYLE, MAP_STYLE_DEFAULT)

    @property
    def gis_basemap(self) -> str:
        return self.entry.options.get(CONF_GIS_BASEMAP, GIS_BASEMAP_DEFAULT)

    async def _async_fetch_text(self, session: aiohttp.ClientSession, url: str) -> str:
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status != 200:
                raise UpdateFailed(f"HTTP {resp.status} for {url}")
            return await resp.text()

    async def _async_update_data(self) -> dict[str, Any]:
        session = async_get_clientsession(self.hass)
        try:
            avertizari_xml = await self._async_fetch_text(session, URL_AVERTIZARI)
        except (aiohttp.ClientError, TimeoutError) as err:
            raise UpdateFailed(f"Avertizări fetch failed: {err}") from err

        nowcasting_xml = ""
        nowcasting_gis_xml = ""
        try:
            nowcasting_xml = await self._async_fetch_text(session, URL_NOWCASTING)
        except (aiohttp.ClientError, TimeoutError, UpdateFailed) as err:
            _LOGGER.warning("Nowcasting fetch failed: %s", err)

        try:
            nowcasting_gis_xml = await self._async_fetch_text(
                session, URL_NOWCASTING_GIS
            )
        except (aiohttp.ClientError, TimeoutError, UpdateFailed) as err:
            _LOGGER.debug("Nowcasting GIS fetch failed: %s", err)

        avertizare_hits = parse_avertizari_xml(avertizari_xml, self.county)
        nowcasting_hits = parse_nowcasting_xml(nowcasting_xml, self.county)
        if nowcasting_gis_xml:
            # GIS feed may duplicate attribute feed; merge unique by (start,end,level,fenomene)
            gis_hits = parse_nowcasting_xml(nowcasting_gis_xml, self.county)
            seen = {
                (h.start, h.end, h.level, h.fenomene[:80]) for h in nowcasting_hits
            }
            for hit in gis_hits:
                key = (hit.start, hit.end, hit.level, hit.fenomene[:80])
                if key not in seen:
                    nowcasting_hits.append(hit)
                    seen.add(key)

        map_ids: list[str] = []
        try:
            page_html = await self._async_fetch_text(session, URL_AVERTIZARI_PAGE)
            map_ids = extract_map_ids_from_html(page_html)
        except (aiohttp.ClientError, TimeoutError, UpdateFailed) as err:
            _LOGGER.warning("Avertizări page (map IDs) fetch failed: %s", err)

        assign_map_ids(avertizare_hits, map_ids)

        # Official SVG paints mountain/litoral sub-zones (e.g. BZ_munte=portocaliu)
        # that are missing from XML county polygons — merge them into GIS GeoJSON.
        await self._async_enrich_hits_with_svg_overlays(session, avertizare_hits)

        # Persist Leaflet assets + GeoJSON under /config/www/cod_galben/
        await async_ensure_gis_assets(self.hass)
        await async_write_warning_geojson(self.hass, avertizare_hits)

        avertizare = summarize_hits(avertizare_hits)
        nowcasting = summarize_hits(nowcasting_hits)
        clear_geojson_from_summary(avertizare)
        clear_geojson_from_summary(nowcasting)

        return {
            "county": self.county,
            "county_name": self.county_name,
            "map_ids": map_ids,
            "map_style": self.map_style,
            "gis_basemap": self.gis_basemap,
            "avertizare": avertizare,
            "nowcasting": nowcasting,
        }

    async def _async_enrich_hits_with_svg_overlays(
        self, session: aiohttp.ClientSession, hits: list
    ) -> None:
        """Fetch ANM SVG per map_id and overlay mountain zones onto geojson."""
        cache: dict[str, str] = {}
        for hit in hits:
            if not hit.geojson or not hit.map_id:
                continue
            map_id = str(hit.map_id)
            if map_id not in cache:
                url = URL_HARTA_SVG.format(id=map_id)
                try:
                    cache[map_id] = await self._async_fetch_text(session, url)
                except (aiohttp.ClientError, TimeoutError, UpdateFailed) as err:
                    _LOGGER.warning("SVG overlay fetch failed for %s: %s", map_id, err)
                    cache[map_id] = ""
            svg_text = cache[map_id]
            if not svg_text:
                continue
            before = len(hit.geojson.get("features") or [])
            hit.geojson = merge_svg_overlays_into_geojson(
                hit.geojson, svg_text, selected_county=self.county
            )
            after = len(hit.geojson.get("features") or [])
            if after > before:
                _LOGGER.debug(
                    "SVG overlays for map %s: +%s features", map_id, after - before
                )
