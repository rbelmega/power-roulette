"""Sensor platform for the Power Roulette integration."""

from __future__ import annotations

from datetime import datetime
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
          NextOutageTextSensor(coordinator, entry),
          ScheduleSensor(coordinator, entry),
          NextRestoreSensor(coordinator, entry),
          NextRestoreTextSensor(coordinator, entry),
      ]
  )


class NextOutageSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Sensor showing the next planned outage."""

  _attr_has_entity_name = True
  _attr_name = "Next outage"
  _attr_icon = "mdi:power-plug-off-outline"
  _attr_device_class = SensorDeviceClass.TIMESTAMP
  _attr_native_precision = 0

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


class NextOutageTextSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Formatted next outage time with relative countdown and local time."""

  _attr_has_entity_name = True
  _attr_name = "Next outage (detailed)"
  _attr_icon = "mdi:clock-alert-outline"

  def __init__(self, coordinator: PowerRouletteCoordinator, entry: ConfigEntry) -> None:
    """Initialize the sensor."""
    super().__init__(coordinator)
    self._entry = entry
    self._attr_unique_id = f"{entry.entry_id}_next_outage_text"
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Power Roulette",
        manufacturer="Power Roulette",
        entry_type=None,
  )

  @property
  def native_value(self) -> Any:
    """Return a string like 'In 4h 23m'."""
    data = self.coordinator.data or {}
    outage_raw = data.get("next_outage")
    if not outage_raw:
      return None
    dt_utc = dt_util.parse_datetime(outage_raw)
    if not dt_utc:
      return None
    now = dt_util.utcnow()
    diff_seconds = (dt_utc - now).total_seconds()
    if diff_seconds < 0:
      return "Now"
    hours = int(diff_seconds // 3600)
    minutes = int((diff_seconds % 3600) // 60)
    return f"In {hours}h {minutes}m"

  @property
  def extra_state_attributes(self) -> dict[str, Any]:
    """Return additional attributes."""
    data = self.coordinator.data or {}
    return {
        "city": data.get("city"),
        "queue": data.get("queue"),
        "next_outage": data.get("next_outage"),
        "retrieved_at": data.get("retrieved_at"),
    }


def _next_restore_datetime(data: dict[str, Any]) -> datetime | None:
  """Return the next restore datetime in UTC if it is in the future."""
  now = dt_util.utcnow()

  def _parse(raw: str | None) -> datetime | None:
    return dt_util.parse_datetime(raw) if raw else None

  restore_dt = _parse(data.get("next_restore"))
  if restore_dt and restore_dt > now:
    return restore_dt

  schedule = data.get("schedule") or []
  next_future_end = None
  for day in schedule:
    for interval in day.get("intervals", []):
      end_dt = _parse(interval.get("end_iso"))
      if not end_dt or end_dt <= now:
        continue
      start_dt = _parse(interval.get("start_iso"))
      if start_dt and start_dt <= now <= end_dt:
        return end_dt
      if not next_future_end or end_dt < next_future_end:
        next_future_end = end_dt

  return next_future_end


class NextRestoreSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Sensor showing when power is expected to return."""

  _attr_has_entity_name = True
  _attr_name = "Next power restore"
  _attr_icon = "mdi:lightning-bolt-circle"
  _attr_device_class = SensorDeviceClass.TIMESTAMP
  _attr_native_precision = 0

  def __init__(self, coordinator: PowerRouletteCoordinator, entry: ConfigEntry) -> None:
    """Initialize the sensor."""
    super().__init__(coordinator)
    self._entry = entry
    self._attr_unique_id = f"{entry.entry_id}_next_restore"
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Power Roulette",
        manufacturer="Power Roulette",
        entry_type=None,
    )

  @property
  def native_value(self) -> Any:
    """Return the next restore time, clamped to a future timestamp when possible."""
    data = self.coordinator.data or {}
    return _next_restore_datetime(data)

  @property
  def extra_state_attributes(self) -> dict[str, Any]:
    """Return attributes."""
    data = self.coordinator.data or {}
    return {
        "city": data.get("city"),
        "queue": data.get("queue"),
        "retrieved_at": data.get("retrieved_at"),
        "current_status": data.get("current_status"),
    }


class NextRestoreTextSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Formatted next restore time with relative countdown."""

  _attr_has_entity_name = True
  _attr_name = "Next power restore (detailed)"
  _attr_icon = "mdi:clock-check-outline"

  def __init__(self, coordinator: PowerRouletteCoordinator, entry: ConfigEntry) -> None:
    """Initialize the sensor."""
    super().__init__(coordinator)
    self._entry = entry
    self._attr_unique_id = f"{entry.entry_id}_next_restore_text"
    self._attr_device_info = DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Power Roulette",
        manufacturer="Power Roulette",
        entry_type=None,
    )

  @property
  def native_value(self) -> Any:
    """Return a string like 'In 4h 23m'."""
    data = self.coordinator.data or {}
    restore_dt = _next_restore_datetime(data)
    if not restore_dt:
      return None
    now = dt_util.utcnow()
    diff_seconds = (restore_dt - now).total_seconds()
    if diff_seconds < 0:
      return "Now"
    hours = int(diff_seconds // 3600)
    minutes = int((diff_seconds % 3600) // 60)
    return f"In {hours}h {minutes}m"

  @property
  def extra_state_attributes(self) -> dict[str, Any]:
    """Return additional attributes."""
    data = self.coordinator.data or {}
    return {
        "city": data.get("city"),
        "queue": data.get("queue"),
        "next_restore": data.get("next_restore"),
        "retrieved_at": data.get("retrieved_at"),
        "current_status": data.get("current_status"),
    }


class ScheduleSensor(CoordinatorEntity[PowerRouletteCoordinator], SensorEntity):
  """Sensor exposing the full outage schedule for charts."""

  _attr_has_entity_name = True
  _attr_name = "Outage schedule"
  _attr_icon = "mdi:chart-timeline-variant"

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
