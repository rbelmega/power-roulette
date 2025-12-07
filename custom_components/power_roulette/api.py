"""API client for the Power Roulette integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Any

from aiohttp import ClientSession
from homeassistant.util import dt as dt_util

from .const import SUPPORTED_CITIES

BASE_URL = "https://be-svitlo.oe.if.ua"
QUEUES_ENDPOINT = "/gpv-queue-list"


class PowerRouletteApiClient:
  """Placeholder API client."""

  def __init__(self, session: ClientSession) -> None:
    """Initialize the client with an aiohttp session."""
    self._session = session

  async def async_get_cities(self) -> list[str]:
    """Return supported cities list (static until API exposes it)."""
    return list(SUPPORTED_CITIES)

  async def async_get_queues(self, city: str | None = None) -> list[str]:
    """Fetch available queues from backend (city is currently informational)."""
    async with self._session.post(f"{BASE_URL}{QUEUES_ENDPOINT}") as resp:
      resp.raise_for_status()
      payload = await resp.json()
    return [item["code"] for item in payload]

  async def async_get_schedule(self, city: str, queue: str | int) -> dict[str, Any]:
    """Return placeholder schedule data for the requested city/queue."""
    # Replace this with a real HTTP call to the blackout schedule service.
    next_outage = dt_util.utcnow() + timedelta(hours=2)
    return {
        "city": city,
        "queue": str(queue),
        "next_outage": next_outage.isoformat(),
        "retrieved_at": dt_util.utcnow().isoformat(),
    }
