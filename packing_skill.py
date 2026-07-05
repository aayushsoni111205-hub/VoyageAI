"""
skills/packing_skill.py
--------------------------
Packing Skill — reusable packing domain logic, extracted out of
agents/packing.py.

See skills/weather_skill.py for the full explanation of why Agent Skills
exist and how this compares to Google ADK's own `Skill` concept. This
module works with plain dicts/lists only (no PackingChecklist/TravelRequest
dependency), so it stays independently testable and reusable.

Capabilities, matching the three areas requested:
    - Packing checklist          (build_baseline_checklist, get_interest_based_items)
    - Weather-based recommendations (get_weather_based_items)
    - Travel reminders           (get_base_reminders, get_conditional_reminders)
"""

from __future__ import annotations

from typing import Dict, List

# Thresholds used to translate raw weather numbers into "hot/cold/rainy/
# humid" flags. Named constants instead of magic numbers in conditionals.
COLD_THRESHOLD_CELSIUS = 15
HOT_THRESHOLD_CELSIUS = 32
HIGH_RAIN_PROBABILITY_PERCENT = 40
HIGH_HUMIDITY_PERCENT = 70


# --------------------------------------------------------------------------
# Packing checklist
# --------------------------------------------------------------------------
_ALWAYS_INCLUDE: Dict[str, List[str]] = {
    "travel_documents": ["Passport / ID"],
    "electronics": ["Phone charger", "Power bank"],
    "miscellaneous": ["Wallet", "Debit/Credit cards", "Reusable water bottle"],
    "medical": ["Personal medication"],
}

_BASE_TRAVEL_DOCUMENTS = ["Travel insurance copy", "Hotel booking confirmation", "Printed/digital tickets"]
_BASE_ELECTRONICS = ["Universal adapter", "Earphones/headphones"]
_BASE_CLOTHING = ["Comfortable everyday outfits", "Sleepwear", "Undergarments (extra pairs)"]
_BASE_FOOTWEAR = ["Comfortable walking shoes"]
_BASE_MEDICAL = ["Basic first-aid kit", "Motion sickness tablets (if needed)"]
_BASE_TOILETRIES = ["Toothbrush & toothpaste", "Travel-size shampoo & soap", "Moisturizer"]
_BASE_FOOD_SNACKS = ["Energy bars or dry snacks for transit", "Electrolyte/rehydration sachets"]

# Interest / trip-type -> category additions.
_INTEREST_ADDITIONS: Dict[str, Dict[str, List[str]]] = {
    "Beaches": {
        "footwear": ["Flip-flops"],
        "clothing": ["Swimwear"],
        "miscellaneous": ["Beach towel", "Waterproof phone pouch"],
    },
    "Adventure": {
        "footwear": ["Trekking shoes"],
        "electronics": ["Power bank (high capacity)", "Torch/headlamp"],
        "adventure_gear": ["First-aid kit", "Multi-tool", "Rain cover for backpack"],
    },
    "Business": {
        "electronics": ["Laptop", "Portable charger"],
        "clothing": ["Formal wear"],
        "miscellaneous": ["Notebook and pen", "Business cards"],
    },
    "Family": {
        "miscellaneous": ["Kids' entertainment/snacks", "Extra wet wipes"],
        "medical": ["Child-safe medication (if applicable)"],
    },
    "Luxury": {
        "clothing": ["Formal evening outfit", "Dress shoes"],
    },
    "Solo": {
        "miscellaneous": ["Portable door lock/travel safety alarm", "Journal"],
    },
}


def build_baseline_checklist() -> Dict[str, List[str]]:
    """
    Skill capability: Packing checklist.

    Returns the always-included baseline, organized by category, before any
    weather- or interest-based additions are layered on.
    """
    return {
        "travel_documents": list(_ALWAYS_INCLUDE["travel_documents"] + _BASE_TRAVEL_DOCUMENTS),
        "electronics": list(_ALWAYS_INCLUDE["electronics"] + _BASE_ELECTRONICS),
        "clothing": list(_BASE_CLOTHING),
        "footwear": list(_BASE_FOOTWEAR),
        "medical": list(_ALWAYS_INCLUDE["medical"] + _BASE_MEDICAL),
        "toiletries": list(_BASE_TOILETRIES),
        "weather_essentials": [],
        "adventure_gear": [],
        "food_snacks": list(_BASE_FOOD_SNACKS),
        "miscellaneous": list(_ALWAYS_INCLUDE["miscellaneous"]),
    }


def get_interest_based_items(interests: List[str]) -> Dict[str, List[str]]:
    """
    Skill capability: Packing checklist (trip-type driven additions).

    Returns a dict of category -> extra items to add, merged across every
    interest the traveler selected (e.g. Beaches + Adventure both contribute).
    """
    additions: Dict[str, List[str]] = {}
    for interest in interests:
        for category, items in _INTEREST_ADDITIONS.get(interest, {}).items():
            additions.setdefault(category, []).extend(items)
    return additions


# --------------------------------------------------------------------------
# Weather-based recommendations
# --------------------------------------------------------------------------
_RAIN_ITEMS = ["Raincoat", "Compact umbrella", "Waterproof shoes", "Dry bag for electronics"]
_COLD_ITEMS = ["Thermal wear", "Woolen cap", "Gloves", "Insulated jacket"]
_HOT_ITEMS = ["Sunscreen (SPF 30+)", "Cap or wide-brim hat", "Cotton/breathable clothes", "Sunglasses"]
_HUMID_ITEMS = ["Quick-dry clothing", "Anti-chafing powder", "Extra pair of socks"]


def get_weather_based_items(
    temperature_celsius: float,
    rain_probability_percent: int,
    humidity_percent: int,
    weather_condition: str,
) -> List[str]:
    """
    Skill capability: Weather-based recommendations.

    Translates raw weather numbers into a flat list of "weather essentials"
    items (rain gear, cold-weather gear, hot-weather gear, humidity gear —
    any combination can apply at once).
    """
    condition_text = weather_condition.lower()
    is_rainy = rain_probability_percent >= HIGH_RAIN_PROBABILITY_PERCENT or "rain" in condition_text
    is_cold = temperature_celsius <= COLD_THRESHOLD_CELSIUS
    is_hot = temperature_celsius >= HOT_THRESHOLD_CELSIUS
    is_humid = humidity_percent >= HIGH_HUMIDITY_PERCENT

    items: List[str] = []
    if is_rainy:
        items.extend(_RAIN_ITEMS)
    if is_cold:
        items.extend(_COLD_ITEMS)
    if is_hot:
        items.extend(_HOT_ITEMS)
    if is_humid:
        items.extend(_HUMID_ITEMS)
    return items


# --------------------------------------------------------------------------
# Travel reminders
# --------------------------------------------------------------------------
_BASE_REMINDERS = [
    "Carry photocopies of important documents.",
    "Keep medicines in your cabin luggage.",
    "Download offline maps for your destination.",
    "Carry some emergency cash in local currency.",
]

_INTEREST_REMINDERS: Dict[str, str] = {
    "Adventure": "Share your trip itinerary with someone before heading out on treks.",
    "Business": "Carry a portable Wi-Fi device and spare business cards.",
    "Family": "Pack a few extra entertainment items to keep kids occupied during transit.",
}


def get_base_reminders() -> List[str]:
    """Skill capability: Travel reminders — reminders that always apply."""
    return list(_BASE_REMINDERS)


def get_conditional_reminders(interests: List[str], rain_probability_percent: int) -> List[str]:
    """
    Skill capability: Travel reminders — reminders triggered by interests or
    weather (e.g. adventure trips, rainy forecasts).
    """
    reminders: List[str] = []
    for interest in interests:
        reminder = _INTEREST_REMINDERS.get(interest)
        if reminder:
            reminders.append(reminder)

    if rain_probability_percent >= HIGH_RAIN_PROBABILITY_PERCENT:
        reminders.append("Keep electronics in a waterproof pouch given the rain forecast.")

    return reminders
