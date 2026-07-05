"""
utils/helpers.py
------------------
Small, reusable, dependency-free helper functions shared by the specialized
agents (Weather, Budget, Itinerary, ...). Centralizing this logic here keeps
individual agents focused on assembling their report, not re-deriving
classification rules, and gives future AI/API integrations a single place to
replace heuristics with real data sources.
"""

from __future__ import annotations

import math
from datetime import date


# --------------------------------------------------------------------------
# Season / climate classification
# --------------------------------------------------------------------------

# Keyword -> climate zone lookup, checked in priority order (coastal first,
# since some cities like Mumbai/Chennai would otherwise also match "urban").
_CLIMATE_ZONE_KEYWORDS: list[tuple[str, list[str]]] = [
    ("coastal", ["goa", "mumbai", "chennai", "kochi", "kerala", "pondicherry",
                 "andaman", "visakhapatnam", "mangalore", "digha", "puri", "gokarna"]),
    ("hill", ["manali", "shimla", "darjeeling", "ooty", "munnar", "nainital",
              "mussoorie", "leh", "ladakh", "kashmir", "sikkim", "kodaikanal",
              "coorg", "dharamshala"]),
    ("desert", ["jaisalmer", "jodhpur", "bikaner", "rajasthan", "thar"]),
    ("urban", ["delhi", "bangalore", "bengaluru", "hyderabad", "pune", "kolkata",
               "ahmedabad", "chandigarh"]),
]


def classify_climate_zone(destination: str) -> str:
    """
    Classify a destination into a coarse climate zone using keyword
    matching. This is a placeholder for a real geocoding/weather-API lookup;
    the return values (zone names) are the contract other code depends on,
    so a future implementation can swap the method body without breaking
    callers.

    Returns one of: "coastal", "hill", "desert", "urban", "plains" (default).
    """
    normalized = destination.strip().lower()
    for zone, keywords in _CLIMATE_ZONE_KEYWORDS:
        if any(keyword in normalized for keyword in keywords):
            return zone
    return "plains"


def get_season(travel_date: date) -> str:
    """
    Map a travel date to a broad Indian seasonal bucket.

    Returns one of: "winter" (Nov-Feb), "summer" (Mar-Jun), "monsoon" (Jul-Oct).
    """
    month = travel_date.month
    if month in (11, 12, 1, 2):
        return "winter"
    if month in (3, 4, 5, 6):
        return "summer"
    return "monsoon"


# --------------------------------------------------------------------------
# Trip-cost helpers
# --------------------------------------------------------------------------

def rooms_required(travelers: int, occupancy_per_room: int = 2) -> int:
    """Compute the number of hotel rooms needed for a given group size."""
    if travelers <= 0:
        return 1
    return math.ceil(travelers / occupancy_per_room)


def dedupe_preserve_order(items: list[str]) -> list[str]:
    """Remove duplicate strings from a list while preserving first-seen order."""
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result
