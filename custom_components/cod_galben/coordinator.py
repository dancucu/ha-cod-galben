"""DataUpdateCoordinator for Cod Galben."""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any

import aiohttp
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import parse_avertizari_xml, parse_nowcasting_xml, summarize_hits
from .const import (
    DOMAIN,
    UPDATE_INTERVAL_SECONDS,
    URL_AVERTIZARI,
    URL_NOWCASTING,
    URL_NOWCASTING_GIS,
    county_label,
)

_LOGGER = logging.getLogger(__name__)


class CodGalbenCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Fetch and parse ANM warnings for one county."""

    def __init__(self, hass: HomeAssistant, county: str) -> None:
        self.county = county.upper()
        self.county_name = county_label(self.county)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{self.county}",
            update_interval=timedelta(seconds=UPDATE_INTERVAL_SECONDS),
        )

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

        return {
            "county": self.county,
            "county_name": self.county_name,
            "avertizare": summarize_hits(avertizare_hits),
            "nowcasting": summarize_hits(nowcasting_hits),
        }
