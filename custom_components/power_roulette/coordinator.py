"""Data update coordinator for the Power Roulette integration."""

from __future__ import annotations

from datetime import timedelta
import logging
from typing import Any

from homeassistant.core import HomeAssistant
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
      return await self.client.async_get_schedule(self.city, self.queue)
    except Exception as err:  # noqa: BLE001 - broad to surface unexpected API issues
      raise UpdateFailed(f"Error communicating with Power Roulette API: {err}") from err
