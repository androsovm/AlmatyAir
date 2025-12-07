import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)


@dataclass
class WeatherData:
    temperature: int  # Celsius
    humidity: int  # %
    wind_speed: float  # m/s
    pressure: int  # hPa

    def format_line(self) -> str:
        return f"🌡 {self.temperature}°C  💧 {self.humidity}%  💨 {self.wind_speed} м/с"


@dataclass
class AirQualityData:
    aqi: int
    main_pollutant: str
    timestamp: datetime
    weather: WeatherData | None = None

    @property
    def level(self) -> str:
        if self.aqi <= 50:
            return "good"
        elif self.aqi <= 100:
            return "moderate"
        elif self.aqi <= 150:
            return "unhealthy_sensitive"
        elif self.aqi <= 200:
            return "unhealthy"
        elif self.aqi <= 300:
            return "very_unhealthy"
        else:
            return "hazardous"

    @property
    def level_emoji(self) -> str:
        levels = {
            "good": "🟢",
            "moderate": "🟡",
            "unhealthy_sensitive": "🟠",
            "unhealthy": "🔴",
            "very_unhealthy": "🟣",
            "hazardous": "🟤",
        }
        return levels.get(self.level, "⚪")

    @property
    def level_text(self) -> str:
        levels = {
            "good": "Хорошее",
            "moderate": "Умеренное",
            "unhealthy_sensitive": "Вредно для чувствительных групп",
            "unhealthy": "Вредно",
            "very_unhealthy": "Очень вредно",
            "hazardous": "Опасно",
        }
        return levels.get(self.level, "Неизвестно")

    @property
    def recommendation(self) -> str:
        recommendations = {
            "good": "Качество воздуха отличное. Можно гулять и заниматься спортом на улице.",
            "moderate": "Качество воздуха приемлемое. Особо чувствительным людям следует ограничить длительное пребывание на улице.",
            "unhealthy_sensitive": "Люди с заболеваниями органов дыхания, пожилые и дети должны ограничить пребывание на улице.",
            "unhealthy": "Всем следует ограничить пребывание на улице, особенно физическую активность.",
            "very_unhealthy": "Избегайте любой активности на улице. Используйте маски и очистители воздуха.",
            "hazardous": "Оставайтесь дома! Качество воздуха опасно для здоровья.",
        }
        return recommendations.get(self.level, "")

    def format_message(self) -> str:
        weather_line = ""
        if self.weather:
            weather_line = f"\n{self.weather.format_line()}\n"

        return (
            f"{self.level_emoji} <b>Качество воздуха в Алматы</b>\n"
            f"{weather_line}\n"
            f"<b>AQI:</b> {self.aqi}\n"
            f"<b>Состояние:</b> {self.level_text}\n"
            f"<b>Основной загрязнитель:</b> {self._format_pollutant()}\n\n"
            f"💡 <i>{self.recommendation}</i>"
        )

    def _format_pollutant(self) -> str:
        pollutants = {
            "p2": "PM2.5 (мелкие частицы)",
            "p1": "PM10 (крупные частицы)",
            "o3": "Озон (O₃)",
            "n2": "Диоксид азота (NO₂)",
            "s2": "Диоксид серы (SO₂)",
            "co": "Угарный газ (CO)",
        }
        return pollutants.get(self.main_pollutant, self.main_pollutant)


class IQAirService:
    BASE_URL = "http://api.airvisual.com/v2"
    CACHE_TTL = timedelta(minutes=10)

    def __init__(self):
        self._cache: AirQualityData | None = None
        self._cache_time: datetime | None = None

    async def get_air_quality(self, force_refresh: bool = False) -> AirQualityData | None:
        # Return cached data if still valid
        if not force_refresh and self._is_cache_valid():
            return self._cache

        try:
            async with aiohttp.ClientSession() as session:
                params = {
                    "city": "Almaty",
                    "state": "Almaty Oblysy",
                    "country": "Kazakhstan",
                    "key": settings.iqair_api_key,
                }

                async with session.get(f"{self.BASE_URL}/city", params=params) as response:
                    if response.status != 200:
                        logger.error(f"IQAir API error: {response.status}")
                        return self._cache  # Return stale cache on error

                    data = await response.json()

                    if data.get("status") != "success":
                        logger.error(f"IQAir API error: {data}")
                        return self._cache

                    current = data["data"]["current"]
                    pollution = current["pollution"]

                    # Parse weather data
                    weather = None
                    if "weather" in current:
                        w = current["weather"]
                        weather = WeatherData(
                            temperature=w.get("tp", 0),
                            humidity=w.get("hu", 0),
                            wind_speed=w.get("ws", 0),
                            pressure=w.get("pr", 0),
                        )

                    air_data = AirQualityData(
                        aqi=pollution["aqius"],
                        main_pollutant=pollution["mainus"],
                        timestamp=datetime.now(),
                        weather=weather,
                    )

                    # Update cache
                    self._cache = air_data
                    self._cache_time = datetime.now()

                    return air_data

        except Exception as e:
            logger.exception(f"Error fetching air quality data: {e}")
            return self._cache

    def _is_cache_valid(self) -> bool:
        if self._cache is None or self._cache_time is None:
            return False
        return datetime.now() - self._cache_time < self.CACHE_TTL


# Singleton instance
iqair_service = IQAirService()
