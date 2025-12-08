"""Constants for the Power Roulette integration."""

from homeassistant.const import Platform

DOMAIN = "power_roulette"
PLATFORMS: list[Platform] = [Platform.SENSOR]
DEFAULT_UPDATE_INTERVAL_MINUTES = 5

# Only Ivano-Frankivsk oblast cities (queues are shared).
IF_CITIES: tuple[str, ...] = (
    "Івано-Франківськ",
    "Коломия",
    "Калуш",
    "Бурштин",
    "Надвірна",
    "Долина",
    "Яремче",
)

LVIV_CITIES: tuple[str, ...] = ()  # kept for compatibility; hidden in UI.

SUPPORTED_CITIES: tuple[str, ...] = IF_CITIES
