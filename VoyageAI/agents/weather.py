"""
agents/weather.py
-------------------
Weather Agent — now backed by skills/weather_skill.py.

Public contract: `generate_weather(request) -> WeatherReport` (unchanged).

This agent is now a thin adapter: it resolves the request into a
(climate_zone, season) pair, calls the reusable Weather Skill for the
actual domain logic (calculations, clothing, warnings), and assembles the
result into the WeatherReport contract every other agent already depends
on. See skills/weather_skill.py for why this logic lives there and how
that compares to Google ADK's own "Skill" concept.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from skills import weather_skill
from utils.helpers import classify_climate_zone, get_season
from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.planner import TravelRequest

logger = get_logger(__name__)


@dataclass
class WeatherReport:
    """Structured weather outlook for a trip."""

    destination: str
    season: str
    temperature_celsius: float
    weather_condition: str
    rain_probability_percent: int
    humidity_percent: int
    wind_speed_kmph: int
    uv_index: int
    recommended_clothing: str
    packing_suggestions: List[str] = field(default_factory=list)
    travel_warning: Optional[str] = None


class WeatherAgent:
    """Specialized agent responsible for the trip's weather outlook."""

    name = "Weather Agent"

    def generate_weather(self, request: "TravelRequest") -> WeatherReport:
        """
        Produce a destination- and season-aware weather outlook by calling
        the Weather Skill for each piece of domain logic and assembling the
        result into a WeatherReport.

        Returns:
            A WeatherReport built from the rule-based Weather Skill. A
            future version can swap the skill's internals for a live
            weather-API call while keeping this method's signature and the
            WeatherReport contract unchanged.
        """
        zone = classify_climate_zone(request.destination)
        season = get_season(request.travel_dates)

        logger.info(
            "%s: destination=%s zone=%s season=%s",
            self.name, request.destination, zone, season,
        )

        # Each of these is an independent Skill capability (see
        # skills/weather_skill.py) — the agent just composes their outputs.
        metrics = weather_skill.calculate_weather_metrics(zone, season)
        recommended_clothing, packing_suggestions = weather_skill.recommend_clothing(zone, season)
        travel_warning = weather_skill.get_travel_warning(zone, season)

        return WeatherReport(
            destination=request.destination,
            season=season,
            temperature_celsius=metrics["temperature_celsius"],
            weather_condition=metrics["weather_condition"],
            rain_probability_percent=metrics["rain_probability_percent"],
            humidity_percent=metrics["humidity_percent"],
            wind_speed_kmph=metrics["wind_speed_kmph"],
            uv_index=metrics["uv_index"],
            recommended_clothing=recommended_clothing,
            packing_suggestions=packing_suggestions,
            travel_warning=travel_warning,
        )
