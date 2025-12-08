"""API client for the Power Roulette integration."""

from __future__ import annotations

from datetime import datetime
import re
from typing import Any, Protocol

from aiohttp import ClientSession

from .const import IF_CITIES, LVIV_CITIES, SUPPORTED_CITIES

# Ivano-Frankivsk provider (public schedule API)
IF_BASE_URL = "https://be-svitlo.oe.if.ua"
IF_QUEUES_ENDPOINT = "/gpv-queue-list"
IF_SCHEDULE_ENDPOINT = "/schedule-by-queue"

# Lviv provider (placeholder; implement with real poweron.loe.lviv.ua endpoints)
LVIV_BASE_URL = "https://poweron.loe.lviv.ua"


class Provider(Protocol):
  """Protocol for per-region providers."""

  async def async_get_queues(self) -> list[str]:
    """Return list of queues."""

  async def async_get_schedule(self, queue: str | int) -> dict[str, Any]:
    """Return normalized schedule for the queue."""


class IvanoFrankivskProvider:
  """Fetch data from be-svitlo.oe.if.ua (Ivano-Frankivsk oblast)."""

  def __init__(self, session: ClientSession) -> None:
    self._session = session

  async def async_get_queues(self) -> list[str]:
    async with self._session.post(f"{IF_BASE_URL}{IF_QUEUES_ENDPOINT}") as resp:
      resp.raise_for_status()
      payload = await resp.json()
    return [item["code"] for item in payload]

  async def async_get_schedule(self, queue: str | int) -> dict[str, Any]:
    params = {"queue": str(queue)}
    async with self._session.get(f"{IF_BASE_URL}{IF_SCHEDULE_ENDPOINT}", params=params) as resp:
      resp.raise_for_status()
      payload = await resp.json()

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
        "schedule": normalized,
    }


class LvivProvider:
  """Provider for Lviv (poweron.loe.lviv.ua) using published photo-graphic schedules."""

  def __init__(self, session: ClientSession) -> None:
    self._session = session

  async def async_get_queues(self) -> list[str]:
    menu = await self._async_get_latest_menu()
    if not menu or not menu.get("rawHtml"):
      # fallback to common groups if parsing fails
      return ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
    text = self._plain_text(menu["rawHtml"])
    groups = sorted({m.group(1) for m in re.finditer(r"Група\s+([0-9.]+)", text)})
    return groups

  async def async_get_schedule(self, queue: str | int) -> dict[str, Any]:
    queue_str = str(queue)
    menu = await self._async_get_latest_menu()
    if not menu or not menu.get("rawHtml"):
      return {"schedule": []}

    raw_html = menu["rawHtml"]
    text = self._plain_text(raw_html)
    event_date = self._extract_date(text)

    group_blocks = re.split(r"(?=Група\s+\d)", text)
    intervals: list[dict[str, Any]] = []
    for block in group_blocks:
      code_match = re.search(r"Група\s+([0-9.]+)", block)
      if not code_match:
        continue
      code = code_match.group(1)
      if code != queue_str:
        continue
      for m in re.finditer(r"з\s*([0-9]{1,2}:[0-9]{2})\s*до\s*([0-9]{1,2}:[0-9]{2})", block):
        start, end = m.group(1), m.group(2)
        if end == "24:00":
          end = "23:59"
        intervals.append(
            {
                "from": start,
                "to": end,
                "status": 1,
                "shutdownHours": f"{start}-{end}",
            }
        )
      break

    schedule: list[dict[str, Any]] = []
    if event_date:
      schedule.append({"event_date": event_date, "intervals": intervals})

    return {"schedule": schedule}

  async def _async_get_latest_menu(self) -> dict[str, Any] | None:
    """Fetch the latest 'photo-grafic' menu entry."""
    async with self._session.get(f"{LVIV_BASE_URL}/api/menus", params={"type": "photo-grafic"}) as resp:
      resp.raise_for_status()
      payload = await resp.json()

    members = payload.get("hydra:member", [])
    if not members:
      return None
    menu_items = members[0].get("menuItems", [])
    # Prefer "Today"
    for item in menu_items:
      if item.get("name", "").lower() == "today" and item.get("rawHtml"):
        return item
    # Fallback: first with rawHtml
    for item in menu_items:
      if item.get("rawHtml"):
        return item
    return None

  def _plain_text(self, html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    return " ".join(text.split())

  def _extract_date(self, text: str) -> str | None:
    m = re.search(r"Графік погодинних відключень на\s+(\d{2}\.\d{2}\.\d{4})", text)
    return m.group(1) if m else None


class PowerRouletteApiClient:
  """API client that routes per-region provider."""

  def __init__(self, session: ClientSession) -> None:
    """Initialize the client with an aiohttp session."""
    self._session = session

  async def async_get_cities(self) -> list[str]:
    """Return currently selectable cities (Ivano-Frankivsk oblast only)."""
    return list(IF_CITIES)

  def _provider_for_city(self, city: str) -> Provider:
    if city in IF_CITIES:
      return IvanoFrankivskProvider(self._session)
    if city in LVIV_CITIES:
      return LvivProvider(self._session)
    raise ValueError(f"City not supported: {city}")

  async def async_get_queues(self, city: str | None = None) -> list[str]:
    """Fetch available queues for a city."""
    if not city:
      return []
    provider = self._provider_for_city(city)
    return await provider.async_get_queues()

  async def async_get_schedule(self, city: str, queue: str | int) -> dict[str, Any]:
    """Fetch blackout schedule for the given queue and normalize."""
    provider = self._provider_for_city(city)
    payload = await provider.async_get_schedule(queue)
    schedule = payload.get("schedule", [])

    return {
        "city": city,
        "queue": str(queue),
        "schedule": schedule,
        "retrieved_at": datetime.utcnow().isoformat(),
    }
