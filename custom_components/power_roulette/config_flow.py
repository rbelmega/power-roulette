"""Config flow for the Power Roulette integration."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import PowerRouletteApiClient
from .const import DOMAIN


class PowerRouletteConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
  """Handle a config flow for Power Roulette."""

  VERSION = 1

  def __init__(self) -> None:
    """Init flow state."""
    self._city: str | None = None
    self._client: PowerRouletteApiClient | None = None

  async def async_step_user(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
    """Handle the initial step."""
    if self._client is None:
      session = async_get_clientsession(self.hass)
      self._client = PowerRouletteApiClient(session)

    errors: dict[str, str] = {}
    if user_input is not None:
      self._city = user_input["city"]
      return await self.async_step_queue()

    try:
      cities = await self._client.async_get_cities()
    except Exception:  # noqa: BLE001 - surface in UI without 500
      errors["base"] = "cannot_connect"
      cities = []

    if cities:
      data_schema = vol.Schema({vol.Required("city"): vol.In(cities)})
    else:
      data_schema = vol.Schema({vol.Required("city"): str})
    return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

  async def async_step_queue(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
    """Select queue for the chosen city."""
    assert self._city  # guarded in previous step
    errors: dict[str, str] = {}

    if user_input is not None:
      queue = user_input["queue"]
      unique_id = f"{self._city.lower()}-{queue}"
      await self.async_set_unique_id(unique_id)
      self._abort_if_unique_id_configured()
      return self.async_create_entry(title=f"{self._city} ({queue})", data={"city": self._city, "queue": queue})

    try:
      queues = await self._client.async_get_queues(self._city)
    except Exception:  # noqa: BLE001
      errors["base"] = "cannot_connect"
      queues = []

    if queues:
      data_schema = vol.Schema({vol.Required("queue"): vol.In(queues)})
    else:
      data_schema = vol.Schema({vol.Required("queue"): str})
    return self.async_show_form(
        step_id="queue",
        data_schema=data_schema,
        errors=errors,
        description_placeholders={"city": self._city},
    )

  @staticmethod
  @callback
  def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
    """Return the options flow handler."""
    return PowerRouletteOptionsFlow(config_entry)


class PowerRouletteOptionsFlow(config_entries.OptionsFlow):
  """Handle options for Power Roulette."""

  def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
    """Initialize options flow."""
    self.config_entry = config_entry
    self._city: str | None = None
    self._client: PowerRouletteApiClient | None = None

  async def async_step_init(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
    """First step of the options flow: pick a city."""
    if self._client is None:
      session = async_get_clientsession(self.hass)
      self._client = PowerRouletteApiClient(session)

    errors: dict[str, str] = {}
    if user_input is not None:
      self._city = user_input["city"]
      return await self.async_step_queue()

    current_city = self.config_entry.options.get("city") or self.config_entry.data.get("city")
    try:
      cities = await self._client.async_get_cities()
    except Exception:  # noqa: BLE001
      errors["base"] = "cannot_connect"
      cities = []

    if cities:
      default_city = current_city if current_city in cities else cities[0]
      data_schema = vol.Schema({vol.Required("city", default=default_city): vol.In(cities)})
    else:
      data_schema = vol.Schema({vol.Required("city", default=current_city): str})
    return self.async_show_form(step_id="init", data_schema=data_schema, errors=errors)

  async def async_step_queue(self, user_input: dict[str, Any] | None = None) -> config_entries.ConfigFlowResult:
    """Second step: pick a queue for the chosen city."""
    assert self._city  # ensured in previous step
    errors: dict[str, str] = {}

    if user_input is not None:
      queue = user_input["queue"]
      return self.async_create_entry(title="", data={"city": self._city, "queue": queue})

    current_queue = self.config_entry.options.get("queue") or self.config_entry.data.get("queue")
    try:
      queues = await self._client.async_get_queues(self._city)
    except Exception:  # noqa: BLE001
      errors["base"] = "cannot_connect"
      queues = []

    if queues:
      default_queue = current_queue if current_queue in queues else queues[0]
      data_schema = vol.Schema({vol.Required("queue", default=default_queue): vol.In(queues)})
    else:
      data_schema = vol.Schema({vol.Required("queue", default=current_queue): str})
    return self.async_show_form(
        step_id="queue",
        data_schema=data_schema,
        errors=errors,
        description_placeholders={"city": self._city},
    )
