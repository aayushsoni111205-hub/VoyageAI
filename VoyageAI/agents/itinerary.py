"""
agents/itinerary.py
---------------------
Day 1 Afternoon — Itinerary Agent (full mock implementation).

Public contract: `create_itinerary(request) -> ItineraryReport`.

Activities are chosen from interest-specific pools (Adventure, Nature,
Luxury, Family, History, Food, Romantic, Business, Solo, Beaches) and
rotated across days so a multi-day, multi-interest trip doesn't repeat the
same plan every day. This pool-based approach is a placeholder for a real
Gemini-generated itinerary — swapping the pool lookup for a Gemini call
later won't require changing ItineraryReport/DayPlan.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Dict, List

from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.planner import TravelRequest

logger = get_logger(__name__)

_DEFAULT_INTEREST = "Solo"


@dataclass
class DayPlan:
    """A single day's plan within an itinerary."""

    day_number: int
    breakfast: str
    morning_activity: str
    lunch: str
    afternoon_activity: str
    evening_activity: str
    dinner: str


@dataclass
class ItineraryReport:
    """Structured, multi-day itinerary for a trip."""

    destination: str
    total_days: int
    daily_plans: List[DayPlan] = field(default_factory=list)
    overview: str = ""
    travel_tips: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Interest -> activity pools. Each pool has independent morning/afternoon/
# evening lists so days can mix-and-match without needing every list to be
# the same length.
# --------------------------------------------------------------------------
_ActivityPool = Dict[str, List[str]]

_ACTIVITY_POOLS: Dict[str, _ActivityPool] = {
    "Adventure": {
        "morning": ["Trekking on a scenic local trail", "Water sports session (jet-ski/parasailing)", "Zipline or rope-course adventure park"],
        "afternoon": ["ATV/off-road ride through nearby terrain", "Rock climbing or rappelling session", "River rafting or kayaking"],
        "evening": ["Bonfire and campsite dinner", "Night trek or stargazing session", "Adventure-sports photo walk"],
    },
    "Nature": {
        "morning": ["Guided nature walk through a nearby reserve", "Birdwatching at a wetland or sanctuary", "Botanical garden or eco-park visit"],
        "afternoon": ["Boat ride through mangroves/backwaters", "Visit to a waterfall or viewpoint", "Nature photography walk"],
        "evening": ["Sunset viewing at a scenic overlook", "Quiet lakeside or riverside walk", "Stargazing away from city lights"],
    },
    "Luxury": {
        "morning": ["Private spa and wellness session", "Leisurely breakfast with a scenic view", "Guided premium heritage tour"],
        "afternoon": ["Fine-dining lunch experience", "Private yacht or boat charter", "Boutique shopping at premium outlets"],
        "evening": ["Rooftop dinner with live music", "Private sunset cruise", "Exclusive cultural performance"],
    },
    "Family": {
        "morning": ["Visit to a family-friendly theme or water park", "Interactive science or children's museum", "Zoo or wildlife park visit"],
        "afternoon": ["Beach or park time with games", "Family-friendly boat ride", "Local craft/pottery workshop"],
        "evening": ["Family dinner with local entertainment", "Evening stroll at a promenade or market", "Movie or games night at the hotel"],
    },
    "History": {
        "morning": ["Guided tour of a historic fort or palace", "Visit to an ancient temple or monument", "Heritage walk through the old town"],
        "afternoon": ["Museum tour covering local history", "Visit to archaeological ruins", "Local heritage craft demonstration"],
        "evening": ["Light-and-sound show at a historic site", "Heritage market walk", "Storytelling session on local legends"],
    },
    "Food": {
        "morning": ["Local food market tour with tastings", "Traditional breakfast trail", "Cooking class featuring local cuisine"],
        "afternoon": ["Street-food crawl through a popular food street", "Regional thali/lunch experience", "Local brewery or beverage tasting"],
        "evening": ["Food-and-culture walking tour", "Dinner at a highly-rated local eatery", "Dessert and café hopping"],
    },
    "Romantic": {
        "morning": ["Leisurely couple's breakfast with a view", "Private couple's spa session", "Scenic drive to a nearby viewpoint"],
        "afternoon": ["Sunset boat ride for two", "Quiet beach or garden picnic", "Wine or coffee tasting for couples"],
        "evening": ["Candlelight dinner with live music", "Private sunset viewing spot", "Evening stroll along a scenic promenade"],
    },
    "Business": {
        "morning": ["Coworking-café breakfast meeting", "Local business district orientation", "Quick visit to a nearby landmark before meetings"],
        "afternoon": ["Buffer time for meetings/calls", "Efficient lunch near the business district", "Networking event or local business meetup"],
        "evening": ["Relaxed dinner near the hotel", "Short unwind walk or gym session", "Light sightseeing near accommodation"],
    },
    "Solo": {
        "morning": ["Self-guided walking tour of the main sights", "Quiet café breakfast and journaling", "Local market exploration at your own pace"],
        "afternoon": ["Visit to a top-rated local attraction", "Solo-friendly group activity or class", "Relaxed café or park time"],
        "evening": ["Sunset viewing at a popular local spot", "Casual dinner at a recommended local eatery", "Evening walk through a lively local area"],
    },
    "Beaches": {
        "morning": ["Relaxed beach morning with swimming", "Beach yoga or a morning walk on the shore", "Snorkeling or glass-bottom boat ride"],
        "afternoon": ["Water sports at a popular beach", "Beach-side lunch with sea view", "Island-hopping boat trip"],
        "evening": ["Sunset at a scenic beach", "Beachside shack dinner", "Beach bonfire and music"],
    },
}


class ItineraryAgent:
    """Specialized agent responsible for the day-wise itinerary."""

    name = "Itinerary Agent"

    def create_itinerary(self, request: "TravelRequest") -> ItineraryReport:
        """
        Produce a day-wise itinerary tailored to the request's interests,
        rotating through selected interests (and through each interest's
        activity pool) so consecutive days don't feel repetitive.

        Returns:
            An ItineraryReport with one DayPlan per day, plus an overview
            and general travel tips.
        """
        interests = request.interests or [_DEFAULT_INTEREST]
        daily_plans = [
            self._build_day_plan(day_number, request.destination, interests)
            for day_number in range(1, request.days + 1)
        ]

        overview = self._build_overview(request, interests)
        travel_tips = self._build_travel_tips(interests)

        logger.info(
            "%s: built %d-day itinerary for %s (interests=%s)",
            self.name, request.days, request.destination, interests,
        )

        return ItineraryReport(
            destination=request.destination,
            total_days=request.days,
            daily_plans=daily_plans,
            overview=overview,
            travel_tips=travel_tips,
        )

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @staticmethod
    def _build_day_plan(day_number: int, destination: str, interests: List[str]) -> DayPlan:
        # Rotate which interest drives this day, then rotate within that
        # interest's pool so a long trip doesn't repeat the same activity.
        interest = interests[(day_number - 1) % len(interests)]
        pool = _ACTIVITY_POOLS.get(interest, _ACTIVITY_POOLS[_DEFAULT_INTEREST])

        morning_index = (day_number - 1) % len(pool["morning"])
        afternoon_index = (day_number - 1) % len(pool["afternoon"])
        evening_index = (day_number - 1) % len(pool["evening"])

        return DayPlan(
            day_number=day_number,
            breakfast=f"Breakfast at a well-reviewed spot near your stay in {destination}",
            morning_activity=pool["morning"][morning_index],
            lunch=f"Lunch at a local {destination} restaurant",
            afternoon_activity=pool["afternoon"][afternoon_index],
            evening_activity=pool["evening"][evening_index],
            dinner=f"Dinner featuring {destination} specialties",
        )

    @staticmethod
    def _build_overview(request: "TravelRequest", interests: List[str]) -> str:
        interests_str = ", ".join(interests)
        return (
            f"{request.destination} offers {request.days} day(s) well suited to "
            f"travelers interested in {interests_str}. This itinerary balances "
            f"key experiences with realistic pacing for a group of {request.travelers} traveler(s)."
        )

    @staticmethod
    def _build_travel_tips(interests: List[str]) -> List[str]:
        tips = [
            "Keep a digital and physical copy of important documents.",
            "Use official/local transport apps for fair pricing.",
            "Carry a reusable water bottle and stay hydrated.",
        ]
        if "Adventure" in interests:
            tips.append("Book adventure activities in advance and confirm safety certifications.")
        if "History" in interests:
            tips.append("Check monument opening hours and dress codes before visiting.")
        if "Food" in interests:
            tips.append("Carry basic digestive medication when trying a lot of street food.")
        if "Romantic" in interests:
            tips.append("Reserve sunset-view spots or tables in advance for popular times.")
        if "Business" in interests:
            tips.append("Confirm venue Wi-Fi and meeting-room availability ahead of time.")
        return tips
