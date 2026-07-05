"""
agents/budget.py
------------------
Budget Agent — now backed by skills/budget_skill.py.

Public contract: `estimate_budget(request) -> BudgetReport` (unchanged).

This agent is now a thin adapter: it resolves the request's hotel tier and
room count, delegates every cost calculation to the reusable Budget Skill,
and assembles the results into the BudgetReport contract every other agent
(Hotel Agent, Planner) already depends on. See skills/budget_skill.py for
why this logic lives there.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict

from skills import budget_skill
from utils.helpers import rooms_required
from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.planner import TravelRequest

logger = get_logger(__name__)


@dataclass
class BudgetReport:
    """Structured, itemized budget estimate for a trip."""

    destination: str
    total_budget: float
    travelers: int
    days: int
    hotel_cost: float
    food_cost: float
    transport_cost: float
    activities_cost: float
    shopping_cost: float
    emergency_fund: float
    miscellaneous_cost: float
    total_estimated_cost: float
    remaining_budget: float
    is_over_budget: bool
    notes: str

    def as_breakdown_dict(self) -> Dict[str, float]:
        """Convenience accessor for UI code (e.g. a pandas DataFrame)."""
        return {
            "Hotel": self.hotel_cost,
            "Food": self.food_cost,
            "Transport": self.transport_cost,
            "Activities": self.activities_cost,
            "Shopping": self.shopping_cost,
            "Emergency Fund": self.emergency_fund,
            "Miscellaneous": self.miscellaneous_cost,
        }


class BudgetAgent:
    """Specialized agent responsible for estimating the trip's budget breakdown."""

    name = "Budget Agent"

    def estimate_budget(self, request: "TravelRequest") -> BudgetReport:
        """
        Produce an itemized, realistic budget estimate for the given
        request by delegating every calculation to the Budget Skill.

        Returns:
            A BudgetReport with per-category costs, total estimated cost,
            and remaining budget (negative if the trip is over budget).
        """
        tier = getattr(request.hotel_preference, "value", "any")
        multiplier = budget_skill.get_tier_multiplier(tier)
        rooms = rooms_required(request.travelers)

        # Expense estimation (Budget Skill)
        hotel_cost = budget_skill.calculate_hotel_cost(tier, rooms, request.days)
        food_cost = budget_skill.calculate_food_cost(request.travelers, request.days, multiplier)
        transport_cost = budget_skill.calculate_transport_cost(request.travelers, request.days)
        activities_cost = budget_skill.calculate_activities_cost(request.travelers, request.days, multiplier)
        shopping_cost = budget_skill.calculate_shopping_cost(request.travelers, request.days)

        # Budget allocation (Budget Skill)
        emergency_fund = budget_skill.allocate_emergency_fund(request.budget)
        miscellaneous_cost = budget_skill.allocate_miscellaneous(request.budget)

        total_estimated_cost = round(
            hotel_cost + food_cost + transport_cost + activities_cost
            + shopping_cost + emergency_fund + miscellaneous_cost,
            2,
        )

        # Remaining budget (Budget Skill)
        remaining_budget, is_over_budget, notes = budget_skill.calculate_remaining_budget(
            request.budget, total_estimated_cost
        )

        logger.info(
            "%s: destination=%s total_estimated=%.2f remaining=%.2f",
            self.name, request.destination, total_estimated_cost, remaining_budget,
        )

        return BudgetReport(
            destination=request.destination,
            total_budget=request.budget,
            travelers=request.travelers,
            days=request.days,
            hotel_cost=hotel_cost,
            food_cost=food_cost,
            transport_cost=transport_cost,
            activities_cost=activities_cost,
            shopping_cost=shopping_cost,
            emergency_fund=emergency_fund,
            miscellaneous_cost=miscellaneous_cost,
            total_estimated_cost=total_estimated_cost,
            remaining_budget=remaining_budget,
            is_over_budget=is_over_budget,
            notes=notes,
        )
