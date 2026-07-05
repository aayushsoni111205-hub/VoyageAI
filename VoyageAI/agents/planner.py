"""
agents/planner.py
-------------------
Day 1 Step 2 — The Planner Agent: the "brain" of VoyageAI.

The Planner Agent never generates travel content itself. Its job is purely
orchestration:

    1. Validate the incoming TravelRequest
    2. Analyze the request to understand intent
    3. Decide which specialized agents are actually required
    4. Execute those agents
    5. Collect their raw outputs
    6. Merge everything into a single structured TravelPlan
    7. Return the final TravelPlan

No agent (including this one) calls Gemini or any external API yet — every
specialized agent currently returns realistic mock data. Swapping mock data
for real Gemini/API calls later (Day 2+) only requires changing what happens
*inside* each specialized agent's public method; the Planner's orchestration
contract (TravelRequest in, TravelPlan out) does not need to change. This is
the extensibility point for Google ADK, Gemini, MCP tools, and live weather/
hotel APIs mentioned in the project brief.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Dict, List, Optional

from agents.budget import BudgetAgent, BudgetReport
from agents.hotel import HotelAgent, HotelRecommendationReport
from agents.itinerary import ItineraryAgent, ItineraryReport
from agents.packing import PackingAgent, PackingChecklist
from agents.weather import WeatherAgent, WeatherReport
from utils.logger import get_logger

logger = get_logger(__name__)


# ==========================================================================
# Enums
# ==========================================================================


class AgentType(Enum):
    """Identifies each specialized agent the Planner can call on."""

    WEATHER = "weather"
    BUDGET = "budget"
    HOTEL = "hotel"
    ITINERARY = "itinerary"
    PACKING = "packing"


# Canonical execution order. Hotel depends on Weather + Budget having already
# run (it factors seasonal booking tips and budget fit into its
# recommendations); Packing depends on Weather (for rain/cold/hot-adapted
# items). Sorting `required_agents` by this order before execution guarantees
# dependencies are satisfied without a full dependency-graph solver.
_AGENT_EXECUTION_ORDER: List[AgentType] = [
    AgentType.WEATHER,
    AgentType.BUDGET,
    AgentType.HOTEL,
    AgentType.ITINERARY,
    AgentType.PACKING,
]

# Which other agents a given agent's public method needs the output of.
_AGENT_DEPENDENCIES: Dict[AgentType, List[AgentType]] = {
    AgentType.HOTEL: [AgentType.WEATHER, AgentType.BUDGET],
    AgentType.PACKING: [AgentType.WEATHER],
}


class TransportPreference(Enum):
    """User's preferred mode of transport to the destination."""

    FLIGHT = "flight"
    TRAIN = "train"
    BUS = "bus"
    CAR = "car"
    ANY = "any"


class HotelPreference(Enum):
    """User's preferred accommodation tier."""

    BUDGET = "budget"
    MID_RANGE = "mid_range"
    LUXURY = "luxury"
    ANY = "any"


# ==========================================================================
# Data models
# ==========================================================================


@dataclass
class TravelRequest:
    """
    Structured representation of a user's travel request.

    This is the single input contract for the Planner Agent. Every field the
    Streamlit UI collects maps 1:1 onto this dataclass, and every
    specialized agent receives the same TravelRequest instance so they all
    reason about the exact same trip.
    """

    source_city: str
    destination: str
    travel_dates: date
    days: int
    budget: float
    travelers: int
    interests: List[str] = field(default_factory=list)
    transport_preference: TransportPreference = TransportPreference.ANY
    hotel_preference: HotelPreference = HotelPreference.ANY
    # Free-text field used by the Planner's intent analysis, e.g. a user
    # typing "I only need a packing list" to narrow which agents run.
    special_requirements: Optional[str] = None


@dataclass
class TravelPlan:
    """
    Structured output of the Planner Agent.

    Every field is optional because the Planner may only have run a subset
    of agents (see `decide_required_agents`). A section left untouched is
    `None` rather than an empty guess, so the UI can clearly show "not
    requested" instead of fabricated content.
    """

    destination_summary: Optional[str] = None
    weather: Optional[WeatherReport] = None
    estimated_budget: Optional[BudgetReport] = None
    hotel_recommendations: Optional[HotelRecommendationReport] = None
    daywise_itinerary: Optional[ItineraryReport] = None
    packing_list: Optional[PackingChecklist] = None
    travel_tips: Optional[List[str]] = None


class TravelRequestValidationError(Exception):
    """Raised when a TravelRequest fails validation before any agent runs."""


# ==========================================================================
# Planner Agent
# ==========================================================================


class PlannerAgent:
    """
    Orchestrator agent. Owns the decision of *which* specialized agents to
    call and *how* to combine their outputs — it holds no travel-domain
    knowledge itself.
    """

    name = "Planner Agent"

    def __init__(self) -> None:
        # Sub-agents are injected as instance attributes rather than created
        # ad hoc inside execute_workflow, so tests (or a future ADK runtime)
        # can substitute real implementations without touching this class.
        self._weather_agent = WeatherAgent()
        self._budget_agent = BudgetAgent()
        self._hotel_agent = HotelAgent()
        self._itinerary_agent = ItineraryAgent()
        self._packing_agent = PackingAgent()

    # ----------------------------------------------------------------
    # Step 1: Validation
    # ----------------------------------------------------------------
    def validate_request(self, request: TravelRequest) -> None:
        """
        Validate a TravelRequest before any agent is executed.

        Raises:
            TravelRequestValidationError: describing the first problem found.
        """
        if not request.destination or not request.destination.strip():
            raise TravelRequestValidationError("Destination is required.")

        if not request.source_city or not request.source_city.strip():
            raise TravelRequestValidationError("Source city is required.")

        if request.days <= 0:
            raise TravelRequestValidationError("Number of days must be greater than 0.")

        if request.budget <= 0:
            raise TravelRequestValidationError("Budget must be greater than 0.")

        if request.travelers < 1:
            raise TravelRequestValidationError("Number of travelers must be at least 1.")

        logger.info("TravelRequest validated: %s -> %s", request.source_city, request.destination)

    # ----------------------------------------------------------------
    # Step 2: Intent analysis
    # ----------------------------------------------------------------
    def analyze_request(self, request: TravelRequest) -> Dict[str, bool]:
        """
        Analyze the request's intent to determine which report sections are
        actually being asked for.

        This currently inspects `special_requirements` for simple keywords
        (e.g. "packing list only"). This is intentionally simple placeholder
        logic — the eventual home for a real Gemini-based intent classifier,
        without changing the method's signature or downstream consumers.

        Returns:
            A dict of intent flags, one per AgentType, e.g.
            {"weather": True, "budget": True, ...}
        """
        text = (request.special_requirements or "").lower()

        # Keyword -> AgentType map used for narrow, single-purpose requests.
        keyword_map = {
            AgentType.WEATHER: ["weather", "forecast", "climate"],
            AgentType.BUDGET: ["budget", "cost", "expense", "price"],
            AgentType.HOTEL: ["hotel", "stay", "accommodation", "resort"],
            AgentType.ITINERARY: ["itinerary", "schedule", "plan my days", "day-wise", "day wise"],
            AgentType.PACKING: ["packing", "pack", "checklist", "what to carry", "what to bring"],
        }

        mentioned = {
            agent_type: any(keyword in text for keyword in keywords)
            for agent_type, keywords in keyword_map.items()
        }
        any_specific_mention = any(mentioned.values())

        # If the user's free text calls out specific sections, honor exactly
        # those. Otherwise assume a "complete trip" request and flag every
        # agent as relevant.
        if any_specific_mention:
            intent = {agent_type.value: is_mentioned for agent_type, is_mentioned in mentioned.items()}
            logger.info("Intent analysis detected narrow request: %s", intent)
        else:
            intent = {agent_type.value: True for agent_type in AgentType}
            logger.info("Intent analysis detected full-trip request.")

        return intent

    # ----------------------------------------------------------------
    # Step 3: Agent selection
    # ----------------------------------------------------------------
    def decide_required_agents(self, request: TravelRequest) -> List[AgentType]:
        """
        Decide which specialized agents must run for this request, then
        expand the selection with any implicit dependencies (e.g. Hotel
        needs Weather + Budget; Packing needs Weather) so downstream agents
        always receive the reports they need.

        Example:
            "I only need a packing list for Goa" -> [Weather, Packing]
            (Weather is pulled in automatically since Packing depends on it)
            A normal full trip request           -> all five agent types
        """
        intent = self.analyze_request(request)
        selected = {agent_type for agent_type in AgentType if intent.get(agent_type.value)}

        # Pull in dependencies for anything selected (single pass is enough
        # since the current dependency graph is only one level deep).
        for agent_type in list(selected):
            for dependency in _AGENT_DEPENDENCIES.get(agent_type, []):
                if dependency not in selected:
                    logger.info(
                        "Adding %s as an implicit dependency of %s", dependency.value, agent_type.value
                    )
                    selected.add(dependency)

        # Return in canonical execution order so callers (and logs) always
        # see a deterministic, dependency-safe sequence.
        required = [agent_type for agent_type in _AGENT_EXECUTION_ORDER if agent_type in selected]

        logger.info(
            "Planner selected agents: %s", [agent_type.value for agent_type in required]
        )
        return required

    # ----------------------------------------------------------------
    # Step 4 & 5: Execution + collection
    # ----------------------------------------------------------------
    def execute_workflow(
        self, request: TravelRequest, required_agents: List[AgentType]
    ) -> Dict[AgentType, object]:
        """
        Execute each required agent, in dependency-safe order, and collect
        their outputs (a dataclass report for every agent implemented so
        far). Hotel and Packing receive the already-computed Weather/Budget
        reports as arguments, matching their public method signatures.

        Returns:
            Mapping of AgentType -> result, containing only the agents that
            were actually selected in `required_agents`.
        """
        raw_results: Dict[AgentType, object] = {}
        ordered_agents = [a for a in _AGENT_EXECUTION_ORDER if a in required_agents]

        for agent_type in ordered_agents:
            logger.info("Executing agent: %s", agent_type.value)

            if agent_type is AgentType.WEATHER:
                raw_results[agent_type] = self._weather_agent.generate_weather(request)
            elif agent_type is AgentType.BUDGET:
                raw_results[agent_type] = self._budget_agent.estimate_budget(request)
            elif agent_type is AgentType.HOTEL:
                weather_report = raw_results[AgentType.WEATHER]
                budget_report = raw_results[AgentType.BUDGET]
                raw_results[agent_type] = self._hotel_agent.recommend_hotels(
                    request, weather_report, budget_report
                )
            elif agent_type is AgentType.ITINERARY:
                raw_results[agent_type] = self._itinerary_agent.create_itinerary(request)
            elif agent_type is AgentType.PACKING:
                weather_report = raw_results[AgentType.WEATHER]
                raw_results[agent_type] = self._packing_agent.create_checklist(request, weather_report)

        return raw_results

    # ----------------------------------------------------------------
    # Step 6: Merge
    # ----------------------------------------------------------------
    def merge_results(self, raw_results: Dict[AgentType, object]) -> TravelPlan:
        """
        Merge raw per-agent results into a single structured TravelPlan.

        Sections whose agent did not run remain None, so the UI can
        distinguish "not requested" from "empty result".
        """
        weather: Optional[WeatherReport] = raw_results.get(AgentType.WEATHER)  # type: ignore[assignment]
        budget: Optional[BudgetReport] = raw_results.get(AgentType.BUDGET)  # type: ignore[assignment]
        hotel: Optional[HotelRecommendationReport] = raw_results.get(AgentType.HOTEL)  # type: ignore[assignment]
        itinerary: Optional[ItineraryReport] = raw_results.get(AgentType.ITINERARY)  # type: ignore[assignment]
        packing: Optional[PackingChecklist] = raw_results.get(AgentType.PACKING)  # type: ignore[assignment]

        # destination_summary and travel_tips are derived from the
        # Itinerary Agent's report, since it already reasons about the
        # destination as a whole. Once dedicated agents exist for these,
        # only this mapping needs to change — TravelPlan's shape stays the
        # same.
        destination_summary = itinerary.overview if itinerary else None
        travel_tips = itinerary.travel_tips if itinerary else None

        plan = TravelPlan(
            destination_summary=destination_summary,
            weather=weather,
            estimated_budget=budget,
            hotel_recommendations=hotel,
            daywise_itinerary=itinerary,
            packing_list=packing,
            travel_tips=travel_tips,
        )

        logger.info("Planner merged results into final TravelPlan.")
        return plan

    # ----------------------------------------------------------------
    # Step 7: Public entrypoint
    # ----------------------------------------------------------------
    def generate_travel_plan(self, request: TravelRequest) -> TravelPlan:
        """
        Full Planner Agent workflow, from raw request to final TravelPlan:

            validate -> analyze -> select agents -> execute -> merge
        """
        self.validate_request(request)
        required_agents = self.decide_required_agents(request)
        raw_results = self.execute_workflow(request, required_agents)
        return self.merge_results(raw_results)
