"""Constants for the Power Roulette integration."""

from homeassistant.const import Platform

DOMAIN = "power_roulette"
PLATFORMS: list[Platform] = [Platform.SENSOR]
DEFAULT_UPDATE_INTERVAL_MINUTES = 5

# Separate providers by region/source (only Ivano-Frankivsk and Lviv oblast).
IF_CITIES: tuple[str, ...] = (
    "Івано-Франківськ",
    "Коломия",
    "Калуш",
    "Бурштин",
    "Надвірна",
    "Долина",
    "Яремче",
)
LVIV_CITIES: tuple[str, ...] = ("Львів",)

SUPPORTED_CITIES: tuple[str, ...] = IF_CITIES + LVIV_CITIES
