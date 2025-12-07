"""API client for the Power Roulette integration."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from aiohttp import ClientSession

from .const import SUPPORTED_CITIES

BASE_URL = "https://be-svitlo.oe.if.ua"
QUEUES_ENDPOINT = "/gpv-queue-list"
SCHEDULE_ENDPOINT = "/schedule-by-queue"


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
    """Fetch blackout schedule for the given queue."""
    params = {"queue": str(queue)}
    async with self._session.get(f"{BASE_URL}{SCHEDULE_ENDPOINT}", params=params) as resp:
      resp.raise_for_status()
      payload = await resp.json()

    # Normalize structure: list of days with intervals for this queue
    normalized: list[dict[str, Any]] = []
    for item in payload:
      event_date = item.get("eventDate")
      queues = item.get("queues", {})
      intervals_raw = queues.get(str(queue), [])
      intervals = []
      for interval in intervals_raw:
        intervals.append(
            {
                "from": interval.get("from"),
                "to": interval.get("to"),
                "status": interval.get("status"),
                "shutdownHours": interval.get("shutdownHours"),
            }
        )
      normalized.append(
          {
              "event_date": event_date,
              "intervals": intervals,
              "created_at": item.get("createdAt"),
              "approved_at": item.get("scheduleApprovedSince"),
          }
      )

    return {
        "city": city,
        "queue": str(queue),
        "schedule": normalized,
        "retrieved_at": datetime.utcnow().isoformat(),
    }
