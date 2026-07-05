"""
skills/budget_skill.py
------------------------
Budget Skill — reusable budget domain logic, extracted out of
agents/budget.py.

See skills/weather_skill.py for the full explanation of why Agent Skills
exist, why they improve reusability/testability, and how this plain-Python
pattern compares to Google ADK's own `Skill` concept. In short: this module
holds pure, stateless functions with no dependency on TravelRequest or
BudgetReport, so any agent (not just BudgetAgent) can reuse the same,
single source of truth for cost math — the Hotel Agent, for example,
already needed its own hotel pricing and previously risked drifting out of
sync with these same rate assumptions.

This skill groups its capabilities into the three areas requested:
    - Expense estimation   (calculate_*_cost functions)
    - Budget allocation    (allocate_* functions)
    - Remaining budget     (calculate_remaining_budget)
"""

from __future__ import annotations

from typing import Dict, Tuple

# --------------------------------------------------------------------------
# Rate constants (named, not magic numbers). All amounts in INR.
# --------------------------------------------------------------------------

HOTEL_RATE_PER_ROOM_PER_NIGHT: Dict[str, float] = {
    "budget": 1200.0,
    "mid_range": 2800.0,
    "luxury": 6000.0,
    "any": 2800.0,
}

# Multiplier applied to food/activity baselines depending on hotel tier,
# since travelers who pick luxury stays also tend to spend more on food
# and activities.
TIER_SPEND_MULTIPLIER: Dict[str, float] = {
    "budget": 0.7,
    "mid_range": 1.0,
    "luxury": 1.6,
    "any": 1.0,
}

_FOOD_BASE_PER_PERSON_PER_DAY = 700.0
_ACTIVITIES_BASE_PER_PERSON_PER_DAY = 500.0
_INTERCITY_TRANSPORT_PER_TRAVELER = 1500.0
_LOCAL_TRANSPORT_PER_PERSON_PER_DAY = 300.0
_SHOPPING_BASE_PER_TRAVELER = 1000.0
_SHOPPING_EXTRA_PER_DAY_BEYOND_3 = 200.0
_SHOPPING_EXTRA_DAY_THRESHOLD = 3
_EMERGENCY_FUND_RATE = 0.05  # 5% of total budget
_MISCELLANEOUS_RATE = 0.03   # 3% of total budget


def get_tier_multiplier(tier: str) -> float:
    """Look up the food/activity spend multiplier for a hotel tier."""
    return TIER_SPEND_MULTIPLIER.get(tier, 1.0)


# --------------------------------------------------------------------------
# Expense estimation
# --------------------------------------------------------------------------

def calculate_hotel_cost(tier: str, rooms: int, days: int) -> float:
    """Skill capability: Expense estimation — hotel cost."""
    nightly_rate = HOTEL_RATE_PER_ROOM_PER_NIGHT.get(tier, HOTEL_RATE_PER_ROOM_PER_NIGHT["any"])
    return round(nightly_rate * rooms * days, 2)


def calculate_food_cost(travelers: int, days: int, multiplier: float) -> float:
    """Skill capability: Expense estimation — food cost."""
    return round(_FOOD_BASE_PER_PERSON_PER_DAY * multiplier * travelers * days, 2)


def calculate_transport_cost(travelers: int, days: int) -> float:
    """Skill capability: Expense estimation — transport cost (intercity + local)."""
    intercity = _INTERCITY_TRANSPORT_PER_TRAVELER * travelers
    local = _LOCAL_TRANSPORT_PER_PERSON_PER_DAY * travelers * days
    return round(intercity + local, 2)


def calculate_activities_cost(travelers: int, days: int, multiplier: float) -> float:
    """Skill capability: Expense estimation — activities cost."""
    return round(_ACTIVITIES_BASE_PER_PERSON_PER_DAY * multiplier * travelers * days, 2)


def calculate_shopping_cost(travelers: int, days: int) -> float:
    """Skill capability: Expense estimation — shopping cost."""
    extra_days = max(0, days - _SHOPPING_EXTRA_DAY_THRESHOLD)
    per_traveler = _SHOPPING_BASE_PER_TRAVELER + extra_days * _SHOPPING_EXTRA_PER_DAY_BEYOND_3
    return round(per_traveler * travelers, 2)


# --------------------------------------------------------------------------
# Budget allocation
# --------------------------------------------------------------------------

def allocate_emergency_fund(total_budget: float) -> float:
    """Skill capability: Budget allocation — emergency fund reserve."""
    return round(total_budget * _EMERGENCY_FUND_RATE, 2)


def allocate_miscellaneous(total_budget: float) -> float:
    """Skill capability: Budget allocation — miscellaneous/incidentals reserve."""
    return round(total_budget * _MISCELLANEOUS_RATE, 2)


# --------------------------------------------------------------------------
# Remaining budget
# --------------------------------------------------------------------------

def calculate_remaining_budget(total_budget: float, total_estimated_cost: float) -> Tuple[float, bool, str]:
    """
    Skill capability: Remaining budget.

    Returns:
        A (remaining_budget, is_over_budget, notes) tuple. `notes` is a
        short, human-readable summary suitable for display as-is.
    """
    remaining_budget = round(total_budget - total_estimated_cost, 2)
    is_over_budget = remaining_budget < 0

    notes = (
        "Estimate exceeds the stated budget — consider a lower hotel tier "
        "or fewer days." if is_over_budget else
        "Estimate fits within the stated budget, with a buffer for "
        "emergencies and incidentals."
    )
    return remaining_budget, is_over_budget, notes
