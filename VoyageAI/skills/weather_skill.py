"""
skills/weather_skill.py
-------------------------
Weather Skill — reusable weather domain logic, extracted out of
agents/weather.py.

============================================================================
WHY AGENT SKILLS EXIST
============================================================================
An "agent" in this project (WeatherAgent, BudgetAgent, ...) has two very
different jobs mixed together if you're not careful:

    1. Orchestration concerns: what input it receives (TravelRequest), what
       structured object it must hand back (WeatherReport), logging, and
       how it fits into the Planner's workflow.
    2. Domain logic: the actual rules that decide "what should the weather
       report say" — climate/season lookups, clothing rules, warnings, etc.

A "Skill" is (2) pulled out into its own module of plain, stateless
functions with no dependency on TravelRequest/WeatherReport or on the
agent's orchestration code at all. The Agent becomes a thin adapter: it
takes the structured request in, calls the Skill functions, and packages
the results back into its structured report.

============================================================================
WHY REUSABLE SKILLS IMPROVE AI AGENTS
============================================================================
- Single source of truth: before this refactor, the weather-matrix data
  used to compute clothing suggestions and travel warnings all lived
  inline inside WeatherAgent.generate_weather(). If another agent ever
  needed "what should someone wear in this climate/season" (e.g. the
  Packing Agent), the only option was to duplicate the lookup table.
  Now any agent (or a future one) can just `import skills.weather_skill`.
- Independently testable: these are pure functions (zone, season) -> data,
  with no TravelRequest object to construct and no logger/agent scaffolding
  to mock. They can be unit tested in isolation.
- Safer to evolve: swapping this rule-based table for a real weather API
  call later only means changing the *inside* of these functions — every
  caller (WeatherAgent, and anything else using the skill) keeps working
  unchanged, because the function signatures don't change.

============================================================================
HOW GOOGLE ADK "SKILLS" WORK (and how this differs)
============================================================================
It's worth being precise here so this isn't misleading: Google's Agent
Development Kit (ADK) has its own, different notion of a "Skill"
(`google.adk.skills`). An ADK Skill is a *packaged capability bundle* for
an LLM-driven agent — a folder containing a `SKILL.md`-style document with
YAML frontmatter (name, description, allowed_tools, ...) plus instructions
and optional resource files. At runtime, an ADK `SkillRegistry` loads or
searches these bundles (`load_skill_from_dir`, `search_skills`) and the
*model itself* decides whether a skill's instructions are relevant and
asks to load them — it's a prompt/instruction-discovery mechanism for an
LLM agent, conceptually similar to how Claude's own Skills work.

This `skills/` folder is a different (and much simpler) idea: it's a plain
Python **software-engineering** pattern — reusable domain-logic modules —
not an ADK `Skill` object. Nothing here is auto-discovered by an LLM at
runtime. We named it "skills" because the *motivation* is the same one
behind ADK's design (give an agent access to a well-defined, reusable
capability instead of baking one-off logic into it), but if this project
later adopts real ADK agents, wiring an actual `google.adk.skills.Skill`
would be a separate, additive step — it would likely just document and
expose the functions below as a callable tool, not replace them.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

# --------------------------------------------------------------------------
# Weather calculations
# --------------------------------------------------------------------------
# Rule-based weather model: (climate_zone, season) -> profile. This is the
# single source of truth for every weather-derived value in the app —
# temperature/condition/rain/humidity/wind/UV, clothing advice, packing
# suggestions, and travel warnings all come from this one table.
_WeatherProfile = Dict[str, object]

_WEATHER_MATRIX: Dict[Tuple[str, str], _WeatherProfile] = {
    ("coastal", "winter"): dict(
        temperature_celsius=28, weather_condition="Sunny and pleasant",
        rain_probability_percent=10, humidity_percent=60, wind_speed_kmph=14, uv_index=7,
        recommended_clothing="Light cotton clothes with a light jacket for evenings",
        packing_suggestions=["Sunglasses", "Sunscreen", "Light jacket"],
        travel_warning=None,
    ),
    ("coastal", "summer"): dict(
        temperature_celsius=33, weather_condition="Hot and humid",
        rain_probability_percent=15, humidity_percent=75, wind_speed_kmph=12, uv_index=9,
        recommended_clothing="Breathable cotton clothes, hats, and sunglasses",
        packing_suggestions=["Hat", "Sunglasses", "Sunscreen", "Extra water bottle"],
        travel_warning="High UV exposure expected — plan beach visits before 11am or after 4pm.",
    ),
    ("coastal", "monsoon"): dict(
        temperature_celsius=27, weather_condition="Rainy with strong winds",
        rain_probability_percent=70, humidity_percent=85, wind_speed_kmph=25, uv_index=4,
        recommended_clothing="Quick-dry clothing with a waterproof layer",
        packing_suggestions=["Raincoat", "Waterproof footwear", "Dry bag for electronics"],
        travel_warning="Rough seas possible — water sports may be restricted.",
    ),
    ("hill", "winter"): dict(
        temperature_celsius=5, weather_condition="Cold, possibly snowy",
        rain_probability_percent=20, humidity_percent=55, wind_speed_kmph=10, uv_index=3,
        recommended_clothing="Heavy woolens, thermal wear, and insulated jacket",
        packing_suggestions=["Thermal wear", "Woolen cap", "Gloves", "Insulated jacket"],
        travel_warning="Road closures possible after heavy snowfall — check routes ahead.",
    ),
    ("hill", "summer"): dict(
        temperature_celsius=18, weather_condition="Cool and pleasant",
        rain_probability_percent=25, humidity_percent=50, wind_speed_kmph=12, uv_index=6,
        recommended_clothing="Light layers with a warm jacket for mornings/evenings",
        packing_suggestions=["Light jacket", "Comfortable walking shoes", "Sunscreen"],
        travel_warning=None,
    ),
    ("hill", "monsoon"): dict(
        temperature_celsius=15, weather_condition="Rainy and misty",
        rain_probability_percent=65, humidity_percent=80, wind_speed_kmph=15, uv_index=3,
        recommended_clothing="Waterproof jacket with warm inner layers",
        packing_suggestions=["Raincoat", "Waterproof shoes", "Umbrella"],
        travel_warning="Landslide risk on hill roads — confirm road status before travel.",
    ),
    ("desert", "winter"): dict(
        temperature_celsius=20, weather_condition="Clear and cool nights",
        rain_probability_percent=5, humidity_percent=30, wind_speed_kmph=10, uv_index=6,
        recommended_clothing="Layered clothing — warm at night, light in the day",
        packing_suggestions=["Light jacket for nights", "Sunglasses", "Moisturizer"],
        travel_warning=None,
    ),
    ("desert", "summer"): dict(
        temperature_celsius=42, weather_condition="Extremely hot and dry",
        rain_probability_percent=2, humidity_percent=20, wind_speed_kmph=18, uv_index=10,
        recommended_clothing="Loose, breathable, light-colored clothing with full sun cover",
        packing_suggestions=["Wide-brim hat", "High-SPF sunscreen", "Electrolyte packets"],
        travel_warning="Extreme heat expected — avoid outdoor activity between noon and 4pm.",
    ),
    ("desert", "monsoon"): dict(
        temperature_celsius=34, weather_condition="Hot with occasional showers",
        rain_probability_percent=25, humidity_percent=40, wind_speed_kmph=16, uv_index=8,
        recommended_clothing="Light cotton clothing with a compact rain layer",
        packing_suggestions=["Compact umbrella", "Sunscreen", "Extra water bottle"],
        travel_warning=None,
    ),
    ("urban", "winter"): dict(
        temperature_celsius=18, weather_condition="Cool and hazy",
        rain_probability_percent=10, humidity_percent=45, wind_speed_kmph=10, uv_index=5,
        recommended_clothing="Light sweaters or jackets, especially for mornings",
        packing_suggestions=["Light jacket", "Moisturizer", "Face mask for pollution-prone days"],
        travel_warning=None,
    ),
    ("urban", "summer"): dict(
        temperature_celsius=36, weather_condition="Hot",
        rain_probability_percent=10, humidity_percent=45, wind_speed_kmph=12, uv_index=9,
        recommended_clothing="Light, breathable clothing",
        packing_suggestions=["Sunglasses", "Sunscreen", "Portable fan or handheld mister"],
        travel_warning="High daytime temperatures — stay hydrated and limit midday outdoor plans.",
    ),
    ("urban", "monsoon"): dict(
        temperature_celsius=29, weather_condition="Humid with heavy showers",
        rain_probability_percent=60, humidity_percent=80, wind_speed_kmph=18, uv_index=5,
        recommended_clothing="Quick-dry clothing with a light raincoat",
        packing_suggestions=["Raincoat", "Waterproof footwear", "Ziplock bags for electronics"],
        travel_warning="Urban waterlogging possible — check local traffic advisories.",
    ),
    ("plains", "winter"): dict(
        temperature_celsius=15, weather_condition="Cold mornings, mild afternoons",
        rain_probability_percent=8, humidity_percent=40, wind_speed_kmph=8, uv_index=4,
        recommended_clothing="Layered warm clothing",
        packing_suggestions=["Warm jacket", "Scarf", "Moisturizer"],
        travel_warning=None,
    ),
    ("plains", "summer"): dict(
        temperature_celsius=38, weather_condition="Hot and dry",
        rain_probability_percent=10, humidity_percent=35, wind_speed_kmph=14, uv_index=9,
        recommended_clothing="Light cotton clothing and sun protection",
        packing_suggestions=["Hat", "Sunglasses", "Sunscreen", "Extra water"],
        travel_warning="High temperatures expected — plan outdoor sightseeing for early morning.",
    ),
    ("plains", "monsoon"): dict(
        temperature_celsius=30, weather_condition="Warm and rainy",
        rain_probability_percent=55, humidity_percent=75, wind_speed_kmph=15, uv_index=5,
        recommended_clothing="Light, quick-dry clothing with a rain layer",
        packing_suggestions=["Umbrella", "Waterproof footwear"],
        travel_warning=None,
    ),
}


def _get_profile(zone: str, season: str) -> _WeatherProfile:
    """Look up the (zone, season) profile, falling back to ('plains', season)."""
    return _WEATHER_MATRIX.get((zone, season), _WEATHER_MATRIX[("plains", season)])


def calculate_weather_metrics(zone: str, season: str) -> Dict[str, object]:
    """
    Skill capability: Weather calculations.

    Returns the raw numeric/condition metrics for a climate zone + season:
    temperature, condition, rain probability, humidity, wind speed, UV index.
    """
    profile = _get_profile(zone, season)
    return {
        "temperature_celsius": profile["temperature_celsius"],
        "weather_condition": profile["weather_condition"],
        "rain_probability_percent": profile["rain_probability_percent"],
        "humidity_percent": profile["humidity_percent"],
        "wind_speed_kmph": profile["wind_speed_kmph"],
        "uv_index": profile["uv_index"],
    }


def recommend_clothing(zone: str, season: str) -> Tuple[str, List[str]]:
    """
    Skill capability: Clothing recommendations.

    Returns a (recommended_clothing, packing_suggestions) tuple for the
    given climate zone + season.
    """
    profile = _get_profile(zone, season)
    return profile["recommended_clothing"], list(profile["packing_suggestions"])


def get_travel_warning(zone: str, season: str) -> Optional[str]:
    """
    Skill capability: Travel warnings.

    Returns a travel warning string for the given climate zone + season, or
    None if there's nothing noteworthy to flag.
    """
    profile = _get_profile(zone, season)
    return profile["travel_warning"]
