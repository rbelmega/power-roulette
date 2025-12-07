"""Sensor platform for the Power Roulette integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import PowerRouletteCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
  """Set up sensors from a config entry."""
  coordinator: PowerRouletteCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
  async_add_entities(
      [
          NextOutageSensor(coordinator, entry),
          ScheduleSensor(coordinator, entry),
      ]
  )


class NextOutageSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Sensor showing the next planned outage."""

  _attr_has_entity_name = True
  _attr_name = "Next outage"
  _attr_device_class = SensorDeviceClass.TIMESTAMP

  def __init__(self, coordinator: PowerRouletteCoordinator, entry: ConfigEntry) -> None:
    """Initialize the sensor."""
    super().__init__(coordinator)
    self._entry = entry
    self._attr_unique_id = f"{entry.entry_id}_next_outage"
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Power Roulette",
        manufacturer="Power Roulette",
        entry_type=None,
    )

  @property
  def native_value(self) -> Any:
    """Return the next outage time."""
    data = self.coordinator.data or {}
    outage_raw = data.get("next_outage")
    if outage_raw:
      return dt_util.parse_datetime(outage_raw)
    return None

  @property
  def extra_state_attributes(self) -> dict[str, Any]:
    """Return additional attributes."""
    data = self.coordinator.data or {}
    return {
        "city": data.get("city"),
        "queue": data.get("queue"),
        "retrieved_at": data.get("retrieved_at"),
    }


class ScheduleSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Sensor exposing the full outage schedule for charts."""

  _attr_has_entity_name = True
  _attr_name = "Outage schedule"

  def __init__(self, coordinator: PowerRouletteCoordinator, entry: ConfigEntry) -> None:
    """Initialize the schedule sensor."""
    super().__init__(coordinator)
    self._entry = entry
    self._attr_unique_id = f"{entry.entry_id}_schedule"
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Power Roulette",
        manufacturer="Power Roulette",
        entry_type=None,
    )

  @property
  def native_value(self) -> str:
    """Return a simple status string."""
    status = (self.coordinator.data or {}).get("current_status", "unknown")
    return status

  @property
  def extra_state_attributes(self) -> dict[str, Any]:
    """Expose schedule for today and tomorrow to be graphed in Lovelace."""
    data = self.coordinator.data or {}
    schedule = data.get("schedule") or []
    return {
        "city": data.get("city"),
        "queue": data.get("queue"),
        "schedule": schedule,
        "next_outage": data.get("next_outage"),
        "next_restore": data.get("next_restore"),
    }
