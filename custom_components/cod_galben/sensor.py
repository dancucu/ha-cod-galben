"""Sensors for Cod Galben."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LEVEL_ICONS, LEVEL_NONE, county_label
from .coordinator import CodGalbenCoordinator


@dataclass(frozen=True, kw_only=True)
class CodGalbenSensorDescription(SensorEntityDescription):
    """Sensor description with value extractor."""

    bucket: str
    value_fn: Callable[[dict[str, Any]], Any]
    attrs: bool = False


def _block(data: dict[str, Any], bucket: str) -> dict[str, Any]:
    return (data or {}).get(bucket) or {}


SENSORS: tuple[CodGalbenSensorDescription, ...] = (
    CodGalbenSensorDescription(
        key="avertizare_nivel",
        name="Nivel avertizare",
        translation_key="avertizare_nivel",
        bucket="avertizare",
        value_fn=lambda b: b.get("nivel") or LEVEL_NONE,
        attrs=True,
    ),
    CodGalbenSensorDescription(
        key="avertizare_fenomene",
        name="Fenomene",
        translation_key="avertizare_fenomene",
        bucket="avertizare",
        value_fn=lambda b: b.get("fenomene") or "Nicio avertizare",
    ),
    CodGalbenSensorDescription(
        key="avertizare_valabil_de",
        name="Valabil de la",
        translation_key="avertizare_valabil_de",
        bucket="avertizare",
        value_fn=lambda b: b.get("valabil_de") or "—",
    ),
    CodGalbenSensorDescription(
        key="avertizare_valabil_pana",
        name="Valabil până la",
        translation_key="avertizare_valabil_pana",
        bucket="avertizare",
        value_fn=lambda b: b.get("valabil_pana") or "—",
    ),
    CodGalbenSensorDescription(
        key="avertizare_interval",
        name="Interval avertizare",
        translation_key="avertizare_interval",
        bucket="avertizare",
        value_fn=lambda b: b.get("interval") or "—",
    ),
    CodGalbenSensorDescription(
        key="avertizare_tip",
        name="Tip mesaj",
        translation_key="avertizare_tip",
        bucket="avertizare",
        value_fn=lambda b: b.get("tip") or "—",
    ),
    CodGalbenSensorDescription(
        key="avertizare_mesaje",
        name="Număr mesaje",
        translation_key="avertizare_mesaje",
        bucket="avertizare",
        value_fn=lambda b: b.get("count") or 0,
    ),
    CodGalbenSensorDescription(
        key="nowcasting_nivel",
        name="Nivel nowcasting",
        translation_key="nowcasting_nivel",
        bucket="nowcasting",
        value_fn=lambda b: b.get("nivel") or LEVEL_NONE,
        attrs=True,
    ),
    CodGalbenSensorDescription(
        key="nowcasting_fenomene",
        name="Fenomene nowcasting",
        translation_key="nowcasting_fenomene",
        bucket="nowcasting",
        value_fn=lambda b: b.get("fenomene") or "Nicio avertizare",
    ),
    CodGalbenSensorDescription(
        key="nowcasting_valabil_de",
        name="Nowcasting de la",
        translation_key="nowcasting_valabil_de",
        bucket="nowcasting",
        value_fn=lambda b: b.get("valabil_de") or "—",
    ),
    CodGalbenSensorDescription(
        key="nowcasting_valabil_pana",
        name="Nowcasting până la",
        translation_key="nowcasting_valabil_pana",
        bucket="nowcasting",
        value_fn=lambda b: b.get("valabil_pana") or "—",
    ),
    CodGalbenSensorDescription(
        key="nowcasting_interval",
        name="Interval nowcasting",
        translation_key="nowcasting_interval",
        bucket="nowcasting",
        value_fn=lambda b: b.get("interval") or "—",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: CodGalbenCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        CodGalbenSensor(coordinator, entry, description) for description in SENSORS
    )


class CodGalbenSensor(CoordinatorEntity[CodGalbenCoordinator], SensorEntity):
    """Cod Galben sensor entity."""

    _attr_has_entity_name = True
    entity_description: CodGalbenSensorDescription

    def __init__(
        self,
        coordinator: CodGalbenCoordinator,
        entry: ConfigEntry,
        description: CodGalbenSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=f"Cod Galben {county_label(coordinator.county)}",
            manufacturer="ANM / Meteoromania",
            model="Avertizări meteo",
            configuration_url="https://www.meteoromania.ro/avertizari/",
        )

    @property
    def native_value(self) -> Any:
        block = _block(self.coordinator.data or {}, self.entity_description.bucket)
        return self.entity_description.value_fn(block)

    @property
    def icon(self) -> str:
        if self.entity_description.key.endswith("_nivel"):
            block = _block(self.coordinator.data or {}, self.entity_description.bucket)
            return LEVEL_ICONS.get(block.get("nivel") or LEVEL_NONE, "mdi:weather-cloudy-alert")
        if "nowcasting" in self.entity_description.key:
            return "mdi:radar"
        return "mdi:weather-cloudy-alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        if not self.entity_description.attrs:
            return {
                "judet": self.coordinator.county,
                "judet_nume": self.coordinator.county_name,
            }
        block = _block(self.coordinator.data or {}, self.entity_description.bucket)
        return {
            "judet": self.coordinator.county,
            "judet_nume": self.coordinator.county_name,
            "fenomene": block.get("fenomene"),
            "valabil_de": block.get("valabil_de"),
            "valabil_pana": block.get("valabil_pana"),
            "interval": block.get("interval"),
            "tip": block.get("tip"),
            "count": block.get("count"),
            "warnings": block.get("warnings"),
        }
