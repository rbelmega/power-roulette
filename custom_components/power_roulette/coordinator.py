"""Data update coordinator for the Power Roulette integration."""

from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import PowerRouletteApiClient
from .const import DEFAULT_UPDATE_INTERVAL_MINUTES, DOMAIN

LOGGER = logging.getLogger(__name__)


class PowerRouletteCoordinator(DataUpdateCoordinator[dict[str, Any]]):
  """Coordinator to poll the Power Roulette API."""

  def __init__(self, hass: HomeAssistant, client: PowerRouletteApiClient, city: str, queue: str | int) -> None:
    """Initialize the coordinator."""
    self.client = client
    self.city = city
    self.queue = queue

    super().__init__(
        hass,
        LOGGER,
        name=f"{DOMAIN}_coordinator",
        update_interval=timedelta(minutes=DEFAULT_UPDATE_INTERVAL_MINUTES),
    )

  async def _async_update_data(self) -> dict[str, Any]:
    """Fetch data from the API."""
    try:
      data = await self.client.async_get_schedule(self.city, self.queue)
      now = dt_util.utcnow()

      # Find the next outage interval across today/tomorrow
      next_outage_iso: str | None = None
      next_restore_iso: str | None = None
      current_status = "on"

      for day in data.get("schedule", []):
        date_str = day.get("event_date")
        if not date_str:
          continue

        def _combine(date_val: str, time_val: str) -> datetime | None:
          """Combine date and time (local tz) into UTC-aware datetime."""
          try:
            local_naive = datetime.strptime(f"{date_val} {time_val}", "%d.%m.%Y %H:%M")
          except ValueError:
            return None
          # Assume schedule times are in HA local timezone
          return dt_util.as_utc(dt_util.as_local(local_naive))

        for interval in day.get("intervals", []):
          start_raw = interval.get("from")
          end_raw = interval.get("to")
          if not start_raw or not end_raw:
            continue
          start_dt = _combine(date_str, start_raw)
          end_dt = _combine(date_str, end_raw)
          if not start_dt or not end_dt:
            continue

          if start_dt > now and (next_outage_iso is None or start_dt.isoformat() < next_outage_iso):
            next_outage_iso = start_dt.isoformat()
            next_restore_iso = end_dt.isoformat()

          if start_dt <= now <= end_dt:
            current_status = "off"

      data["next_outage"] = next_outage_iso
      data["next_restore"] = next_restore_iso
      data["current_status"] = current_status
      return data
    except Exception as err:  # noqa: BLE001 - broad to surface unexpected API issues
      raise UpdateFailed(f"Error communicating with Power Roulette API: {err}") from err
