"""Constants for the Power Roulette integration."""

from homeassistant.const import Platform

DOMAIN = "power_roulette"
PLATFORMS: list[Platform] = [Platform.SENSOR]
DEFAULT_UPDATE_INTERVAL_MINUTES = 5
# Ivano-Frankivsk Oblast cities supported by the public schedule API.
SUPPORTED_CITIES: tuple[str, ...] = (
    "Івано-Франківськ",
    "Коломия",
    "Калуш",
    "Бурштин",
    "Надвірна",
    "Долина",
    "Яремче",
)
