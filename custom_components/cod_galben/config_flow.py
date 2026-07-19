"""Config flow for Cod Galben."""

from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import SelectSelector, SelectSelectorConfig

from .const import CONF_COUNTY, DOMAIN, JUDETE, NAME, county_label


def _county_options() -> list[dict[str, str]]:
    return [
        {"value": code, "label": f"{name} ({code})"}
        for code, name in sorted(JUDETE.items(), key=lambda item: item[1])
    ]


class CodGalbenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Cod Galben."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Select Romanian county."""
        errors: dict[str, str] = {}

        if user_input is not None:
            county = user_input[CONF_COUNTY].upper()
            if county not in JUDETE:
                errors["base"] = "invalid_county"
            else:
                await self.async_set_unique_id(f"{DOMAIN}_{county}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"{NAME} — {county_label(county)}",
                    data={CONF_COUNTY: county},
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_COUNTY): SelectSelector(
                    SelectSelectorConfig(
                        options=_county_options(),
                        mode="dropdown",
                    )
                ),
            }
        )
        return self.async_show_form(
            step_id="user", data_schema=schema, errors=errors
        )
