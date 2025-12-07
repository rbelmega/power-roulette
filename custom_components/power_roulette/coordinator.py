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
      tz = dt_util.get_time_zone(self.hass.config.time_zone)

      def _combine(date_val: str, time_val: str) -> datetime | None:
        """Combine date and time (local tz) into UTC-aware datetime."""
        try:
          local_naive = datetime.strptime(f"{date_val} {time_val}", "%d.%m.%Y %H:%M")
        except ValueError:
          return None
        local_dt = local_naive.replace(tzinfo=tz)
        return dt_util.as_utc(local_dt)

      intervals_all: list[tuple[datetime, datetime]] = []

      for day in data.get("schedule", []):
        date_str = day.get("event_date")
        if not date_str:
          continue

        for interval in day.get("intervals", []):
          start_raw = interval.get("from")
          end_raw = interval.get("to")
          if not start_raw or not end_raw:
            continue
          start_dt = _combine(date_str, start_raw)
          end_dt = _combine(date_str, end_raw)
          if not start_dt or not end_dt:
            continue
          # If the interval crosses midnight, push the end to the next day.
          if end_dt <= start_dt:
            end_dt = end_dt + timedelta(days=1)

          # Persist normalized datetimes for UI cards
          interval["start_iso"] = start_dt.isoformat()
          interval["end_iso"] = end_dt.isoformat()
          intervals_all.append((start_dt, end_dt))

      intervals_all.sort(key=lambda pair: pair[0])

      next_outage_iso: str | None = None
      next_restore_iso: str | None = None
      current_status = "on"

      for start_dt, end_dt in intervals_all:
        if now < end_dt:
          next_outage_iso = start_dt.isoformat()
          next_restore_iso = end_dt.isoformat()
          if start_dt <= now:
            current_status = "off"
          break

      data["next_outage"] = next_outage_iso
      data["next_restore"] = next_restore_iso
      data["current_status"] = current_status
      return data
    except Exception as err:  # noqa: BLE001 - broad to surface unexpected API issues
      raise UpdateFailed(f"Error communicating with Power Roulette API: {err}") from err
