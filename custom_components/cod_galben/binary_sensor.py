"""Binary sensors for Cod Galben."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LEVEL_ICONS, county_label
from .coordinator import CodGalbenCoordinator

BINARY_SENSORS = (
    BinarySensorEntityDescription(
        key="avertizare_afectat",
        name="Avertizare activă",
        translation_key="avertizare_afectat",
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
    BinarySensorEntityDescription(
        key="nowcasting_afectat",
        name="Nowcasting activ",
        translation_key="nowcasting_afectat",
        device_class=BinarySensorDeviceClass.SAFETY,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CodGalbenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CodGalbenBinarySensor(coordinator, entry, description)
        for description in BINARY_SENSORS
    )


class CodGalbenBinarySensor(CoordinatorEntity[CodGalbenCoordinator], BinarySensorEntity):
    """Binary sensor: county currently under a warning."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: CodGalbenCoordinator,
        entry: ConfigEntry,
        description: BinarySensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        county = coordinator.county
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cod Galben {county_label(county)}",
            manufacturer="ANM / Meteoromania",
            model="Avertizări meteo",
            configuration_url="https://www.meteoromania.ro/avertizari/",
        )

    @property
    def is_on(self) -> bool:
        bucket = (
            "avertizare"
            if self.entity_description.key.startswith("avertizare")
            else "nowcasting"
        )
        data = self.coordinator.data or {}
        return bool((data.get(bucket) or {}).get("afectat"))

    @property
    def icon(self) -> str:
        bucket = (
            "avertizare"
            if self.entity_description.key.startswith("avertizare")
            else "nowcasting"
        )
        nivel = ((self.coordinator.data or {}).get(bucket) or {}).get("nivel", "none")
        if self.is_on:
            return LEVEL_ICONS.get(nivel, "mdi:alert")
        return "mdi:check-circle-outline"

    @property
    def extra_state_attributes(self) -> dict:
        bucket = (
            "avertizare"
            if self.entity_description.key.startswith("avertizare")
            else "nowcasting"
        )
        block = (self.coordinator.data or {}).get(bucket) or {}
        data = self.coordinator.data or {}
        return {
            "nivel": block.get("nivel"),
            "fenomene": block.get("fenomene"),
            "valabil_de": block.get("valabil_de"),
            "valabil_pana": block.get("valabil_pana"),
            "interval": block.get("interval"),
            "tip": block.get("tip"),
            "mesaj": block.get("mesaj"),
            "count": block.get("count"),
            "map_ids": block.get("map_ids") or data.get("map_ids") or [],
            "warnings": block.get("warnings"),
            "judet": self.coordinator.county,
            "judet_nume": self.coordinator.county_name,
        }
