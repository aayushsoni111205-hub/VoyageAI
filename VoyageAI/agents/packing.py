"""
agents/packing.py
-------------------
Packing Agent — now backed by skills/packing_skill.py.

Public contract:
    create_checklist(request, weather) -> PackingChecklist   (unchanged)

This agent is now a thin adapter: it calls the reusable Packing Skill for
checklist building, weather-based recommendations, and travel reminders,
then assembles the results into the PackingChecklist/TravelReminder
contracts the rest of the app depends on (app.py, tools/pdf_generator.py).
See skills/packing_skill.py for why this logic lives there.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List

from agents.weather import WeatherReport
from skills import packing_skill
from utils.helpers import dedupe_preserve_order
from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.planner import TravelRequest

logger = get_logger(__name__)


@dataclass
class TravelReminder:
    """A single actionable reminder shown alongside the packing checklist."""

    message: str


@dataclass
class PackingChecklist:
    """Structured, categorized packing checklist for a trip."""

    destination: str
    travel_documents: List[str] = field(default_factory=list)
    electronics: List[str] = field(default_factory=list)
    clothing: List[str] = field(default_factory=list)
    footwear: List[str] = field(default_factory=list)
    medical: List[str] = field(default_factory=list)
    toiletries: List[str] = field(default_factory=list)
    weather_essentials: List[str] = field(default_factory=list)
    adventure_gear: List[str] = field(default_factory=list)
    food_snacks: List[str] = field(default_factory=list)
    miscellaneous: List[str] = field(default_factory=list)
    travel_reminders: List[TravelReminder] = field(default_factory=list)


class PackingAgent:
    """Specialized agent responsible for the trip's packing checklist."""

    name = "Packing Agent"

    def create_checklist(self, request: "TravelRequest", weather: WeatherReport) -> PackingChecklist:
        """
        Build a categorized packing checklist by composing three Packing
        Skill capabilities: the baseline/interest-driven checklist,
        weather-based recommendations, and travel reminders.

        Returns:
            A PackingChecklist with one list per category plus travel
            reminders.
        """
        # 1. Packing checklist (baseline + interest-driven additions)
        categories = packing_skill.build_baseline_checklist()
        interest_additions = packing_skill.get_interest_based_items(request.interests)
        for category, items in interest_additions.items():
            categories.setdefault(category, []).extend(items)

        # 2. Weather-based recommendations
        categories["weather_essentials"].extend(
            packing_skill.get_weather_based_items(
                temperature_celsius=weather.temperature_celsius,
                rain_probability_percent=weather.rain_probability_percent,
                humidity_percent=weather.humidity_percent,
                weather_condition=weather.weather_condition,
            )
        )

        # 3. Travel reminders
        reminder_messages = packing_skill.get_base_reminders()
        reminder_messages.extend(
            packing_skill.get_conditional_reminders(request.interests, weather.rain_probability_percent)
        )

        # De-duplicate every category in case weather + interest logic both
        # added the same item.
        for category in categories:
            categories[category] = dedupe_preserve_order(categories[category])
        reminder_messages = dedupe_preserve_order(reminder_messages)

        logger.info("%s: built checklist for %s", self.name, request.destination)

        return PackingChecklist(
            destination=request.destination,
            travel_documents=categories["travel_documents"],
            electronics=categories["electronics"],
            clothing=categories["clothing"],
            footwear=categories["footwear"],
            medical=categories["medical"],
            toiletries=categories["toiletries"],
            weather_essentials=categories["weather_essentials"],
            adventure_gear=categories["adventure_gear"],
            food_snacks=categories["food_snacks"],
            miscellaneous=categories["miscellaneous"],
            travel_reminders=[TravelReminder(message=m) for m in reminder_messages],
        )
