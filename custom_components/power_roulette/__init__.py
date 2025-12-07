"""Setup for the Power Roulette integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.typing import ConfigType

from .api import PowerRouletteApiClient
from .const import DOMAIN, PLATFORMS
from .coordinator import PowerRouletteCoordinator

LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
  """Set up the integration via YAML (not supported)."""
  return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  """Set up Power Roulette from a config entry."""
  hass.data.setdefault(DOMAIN, {})

  session = async_get_clientsession(hass)
  client = PowerRouletteApiClient(session)
  coordinator = PowerRouletteCoordinator(hass, client, entry.data["city"], entry.data["queue"])

  await coordinator.async_config_entry_first_refresh()

  hass.data[DOMAIN][entry.entry_id] = {
      "coordinator": coordinator,
  }

  await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
  return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
  """Unload a config entry."""
  unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

  if unload_ok:
    hass.data[DOMAIN].pop(entry.entry_id, None)

  return unload_ok
