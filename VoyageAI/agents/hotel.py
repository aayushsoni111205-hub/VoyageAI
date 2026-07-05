"""
agents/hotel.py
-----------------
Day 2 Morning — Hotel Agent (full mock implementation).

Public contract:
    recommend_hotels(request, weather, budget) -> HotelRecommendationReport

Recommendations are built from a "travel style" pool (Budget, Standard,
Luxury, Family, Solo, Business, Romantic, Adventure) selected from the
traveler's interests and hotel preference, combined with pricing derived
from named rate constants. No hotel-search API or Gemini call yet — a
future version replaces the pool lookup below with a real API/MCP call
while keeping the HotelRecommendationReport contract unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from statistics import mean
from typing import TYPE_CHECKING, Dict, List

from agents.budget import BudgetReport
from agents.weather import WeatherReport
from utils.helpers import rooms_required
from utils.logger import get_logger

if TYPE_CHECKING:
    from agents.planner import TravelRequest

logger = get_logger(__name__)


@dataclass
class HotelRecommendation:
    """A single recommended place to stay."""

    hotel_name: str
    hotel_category: str
    price_per_night: float
    estimated_total_cost: float
    rating: float
    amenities: List[str] = field(default_factory=list)
    distance_from_city_center: str = ""
    best_for: str = ""
    short_description: str = ""


@dataclass
class HotelRecommendationReport:
    """Structured hotel recommendations for a trip."""

    destination: str
    recommended_hotels: List[HotelRecommendation] = field(default_factory=list)
    best_value_hotel: HotelRecommendation = None  # type: ignore[assignment]
    budget_summary: str = ""
    booking_tips: List[str] = field(default_factory=list)


# --------------------------------------------------------------------------
# Style pools. Each style has 3 hotel templates; a "Standard" pool of 5 pads
# out any style's list to a total of 5 recommendations.
# --------------------------------------------------------------------------
_HotelTemplate = Dict[str, object]

_STANDARD_POOL: List[_HotelTemplate] = [
    {"name": "{dest} City Comfort Hotel", "amenities": ["Free WiFi", "AC rooms", "24/7 front desk"],
     "best_for": "Most travelers", "description": "A reliable, well-located mid-range stay."},
    {"name": "{dest} Central Inn", "amenities": ["Free WiFi", "Breakfast included", "Room service"],
     "best_for": "Convenience seekers", "description": "Centrally located with easy access to attractions."},
    {"name": "{dest} Skyline Hotel", "amenities": ["Free WiFi", "Restaurant on-site", "Airport shuttle"],
     "best_for": "Travelers wanting extra comfort", "description": "A dependable option with solid amenities."},
    {"name": "{dest} Garden View Hotel", "amenities": ["Free WiFi", "Garden seating", "Parking available"],
     "best_for": "Travelers who value a quiet stay", "description": "A calm option away from the busiest streets."},
    {"name": "{dest} Metro Stay", "amenities": ["Free WiFi", "Close to transit", "24/7 front desk"],
     "best_for": "Travelers without a car", "description": "Easy access to public transport and local sights."},
]

_STYLE_POOLS: Dict[str, List[_HotelTemplate]] = {
    "Budget": [
        {"name": "{dest} Backpackers Hostel", "amenities": ["Free WiFi", "Shared kitchen", "Locker storage"],
         "best_for": "Budget-conscious travelers", "description": "A clean, sociable hostel that keeps costs low."},
        {"name": "{dest} Comfort Guest House", "amenities": ["Free WiFi", "Fan/AC rooms", "Home-style meals"],
         "best_for": "Travelers wanting a homely stay", "description": "Simple, affordable, and friendly."},
        {"name": "{dest} City View 3-Star Hotel", "amenities": ["Free WiFi", "AC rooms", "Daily housekeeping"],
         "best_for": "Value-focused travelers", "description": "A no-frills hotel with everything you need."},
    ],
    "Luxury": [
        {"name": "{dest} Grand 5-Star Resort", "amenities": ["Spa", "Infinity pool", "Fine dining", "Valet parking"],
         "best_for": "Travelers wanting a premium experience", "description": "A top-tier resort with world-class service."},
        {"name": "{dest} Beachfront Luxury Resort", "amenities": ["Private beach access", "Spa", "Multiple restaurants"],
         "best_for": "Travelers seeking indulgence", "description": "Elevated comfort with stunning views."},
        {"name": "{dest} Boutique Heritage Hotel", "amenities": ["Curated decor", "Rooftop lounge", "Personal concierge"],
         "best_for": "Travelers who love unique stays", "description": "A characterful, upscale boutique property."},
    ],
    "Family": [
        {"name": "{dest} Family Suites Resort", "amenities": ["Connecting rooms", "Kids' pool", "Family dining"],
         "best_for": "Families with children", "description": "Spacious suites designed for family comfort."},
        {"name": "{dest} Kids-Friendly Resort", "amenities": ["Kids' club", "Play area", "Babysitting on request"],
         "best_for": "Families traveling with young kids", "description": "Keeps the whole family entertained and comfortable."},
        {"name": "{dest} Serviced Apartments", "amenities": ["Kitchenette", "Laundry", "Multiple bedrooms"],
         "best_for": "Larger families or longer stays", "description": "Home-like space with room to unwind."},
    ],
    "Solo": [
        {"name": "{dest} Backpacker Hostel", "amenities": ["Free WiFi", "Common lounge", "Locker storage"],
         "best_for": "Solo travelers who enjoy meeting people", "description": "Social atmosphere with budget-friendly pricing."},
        {"name": "{dest} Capsule Hotel", "amenities": ["Free WiFi", "Compact pods", "24/7 access"],
         "best_for": "Solo travelers wanting privacy on a budget", "description": "Efficient, modern, and surprisingly comfortable."},
        {"name": "{dest} Smart Business Hotel", "amenities": ["Free WiFi", "Work desk", "Self-service check-in"],
         "best_for": "Solo travelers who value convenience", "description": "A no-fuss stay with everything essential."},
    ],
    "Business": [
        {"name": "{dest} Business Hotel", "amenities": ["Free WiFi", "Business center", "Meeting rooms"],
         "best_for": "Business travelers", "description": "Efficient and well-connected for work trips."},
        {"name": "{dest} Conference & Suites Hotel", "amenities": ["Conference halls", "High-speed WiFi", "Airport shuttle"],
         "best_for": "Travelers attending events or meetings", "description": "Purpose-built for productive stays."},
        {"name": "{dest} Executive Rooms Hotel", "amenities": ["Executive lounge", "Work desk", "Laundry service"],
         "best_for": "Frequent business travelers", "description": "Premium comfort tailored to work trips."},
    ],
    "Romantic": [
        {"name": "{dest} Couple's Boutique Resort", "amenities": ["Private balcony", "Candlelight dining", "Spa for two"],
         "best_for": "Couples", "description": "An intimate, romantic setting for two."},
        {"name": "{dest} Romantic Villa Stay", "amenities": ["Private pool", "Personal butler", "Sunset views"],
         "best_for": "Couples wanting privacy", "description": "A secluded villa perfect for quality time together."},
        {"name": "{dest} Honeymoon Suites Resort", "amenities": ["Jacuzzi", "Room decoration on request", "Private dining"],
         "best_for": "Honeymooners and anniversaries", "description": "Designed for special romantic occasions."},
    ],
    "Adventure": [
        {"name": "{dest} Adventure Base Camp Lodge", "amenities": ["Gear storage", "Guide desk", "Hearty breakfast"],
         "best_for": "Adventure travelers", "description": "A practical base for early starts and outdoor days."},
        {"name": "{dest} Eco Trekker's Lodge", "amenities": ["Nature trails nearby", "Bonfire area", "Simple comfortable rooms"],
         "best_for": "Trekkers and nature lovers", "description": "Close to trailheads with a rustic, outdoorsy feel."},
        {"name": "{dest} Riverside Adventure Resort", "amenities": ["Activity desk", "Outdoor seating", "Equipment rental"],
         "best_for": "Groups planning outdoor activities", "description": "Convenient for water sports and outdoor excursions."},
    ],
}

# Base nightly rate per style (INR). Distinct from BudgetAgent's tier rates,
# since a hotel's style (e.g. Luxury resort vs Business hotel) drives price
# more precisely than the coarse hotel_preference tier alone.
_STYLE_BASE_RATE: Dict[str, float] = {
    "Budget": 1200.0, "Standard": 2800.0, "Luxury": 6000.0, "Family": 3200.0,
    "Solo": 1800.0, "Business": 4500.0, "Romantic": 4000.0, "Adventure": 2500.0,
}
_STYLE_BASE_RATING: Dict[str, float] = {
    "Budget": 4.1, "Standard": 4.2, "Luxury": 4.7, "Family": 4.4,
    "Solo": 4.1, "Business": 4.5, "Romantic": 4.6, "Adventure": 4.3,
}
_PRICE_VARIATION_PER_INDEX = 0.08
_RATING_VARIATION_PER_INDEX = 0.05
_MAX_RATING = 4.9
_MIN_RATING = 4.0
_DISTANCE_CYCLE = ["0.4 km", "1.1 km", "2.3 km", "3.6 km", "5.0 km"]

# Interests -> style, checked in priority order so the most specific style
# wins when a traveler selects multiple interests.
_STYLE_PRIORITY: List[str] = ["Family", "Business", "Romantic", "Adventure", "Luxury", "Solo"]


class HotelAgent:
    """Specialized agent responsible for accommodation recommendations."""

    name = "Hotel Agent"

    def recommend_hotels(
        self, request: "TravelRequest", weather: WeatherReport, budget: BudgetReport
    ) -> HotelRecommendationReport:
        """
        Produce 3-5 hotel recommendations tailored to the traveler's style,
        budget tier, and trip length, using the Weather and Budget reports
        for context-aware booking tips and a fit-vs-budget summary.

        Returns:
            A HotelRecommendationReport with recommended hotels, the best
            value pick, a budget-fit summary, and booking tips.
        """
        style = self._determine_style(request)
        templates = self._build_template_list(style)
        rooms = rooms_required(request.travelers)

        hotels = [
            self._build_recommendation(template, style if index < 3 else "Standard", index, request, rooms)
            for index, template in enumerate(templates)
        ]

        best_value = max(hotels, key=lambda h: h.rating / h.price_per_night)
        budget_summary = self._build_budget_summary(hotels, budget, request.days)
        booking_tips = self._build_booking_tips(request, weather)

        logger.info(
            "%s: style=%s recommended %d hotels for %s",
            self.name, style, len(hotels), request.destination,
        )

        return HotelRecommendationReport(
            destination=request.destination,
            recommended_hotels=hotels,
            best_value_hotel=best_value,
            budget_summary=budget_summary,
            booking_tips=booking_tips,
        )

    # ------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------
    @staticmethod
    def _determine_style(request: "TravelRequest") -> str:
        for style in _STYLE_PRIORITY:
            if style in request.interests:
                return style
        tier = getattr(request.hotel_preference, "value", "any")
        if tier == "budget":
            return "Budget"
        if tier == "luxury":
            return "Luxury"
        return "Standard"

    @staticmethod
    def _build_template_list(style: str) -> List[_HotelTemplate]:
        if style == "Standard":
            return _STANDARD_POOL[:5]
        primary = _STYLE_POOLS.get(style, _STANDARD_POOL[:3])
        padding = [t for t in _STANDARD_POOL if t not in primary][:2]
        return primary + padding

    @staticmethod
    def _build_recommendation(
        template: _HotelTemplate, category: str, index: int,
        request: "TravelRequest", rooms: int,
    ) -> HotelRecommendation:
        base_rate = _STYLE_BASE_RATE.get(category, _STYLE_BASE_RATE["Standard"])
        base_rating = _STYLE_BASE_RATING.get(category, _STYLE_BASE_RATING["Standard"])

        price_per_night = round(base_rate * (1 + index * _PRICE_VARIATION_PER_INDEX), 2)
        rating = round(
            min(_MAX_RATING, max(_MIN_RATING, base_rating + index * _RATING_VARIATION_PER_INDEX)), 1
        )
        estimated_total_cost = round(price_per_night * rooms * request.days, 2)

        return HotelRecommendation(
            hotel_name=str(template["name"]).format(dest=request.destination),
            hotel_category=category,
            price_per_night=price_per_night,
            estimated_total_cost=estimated_total_cost,
            rating=rating,
            amenities=list(template["amenities"]),  # type: ignore[arg-type]
            distance_from_city_center=_DISTANCE_CYCLE[index % len(_DISTANCE_CYCLE)],
            best_for=str(template["best_for"]),
            short_description=str(template["description"]),
        )

    @staticmethod
    def _build_budget_summary(hotels: List[HotelRecommendation], budget: BudgetReport, days: int) -> str:
        average_cost = round(mean(h.estimated_total_cost for h in hotels), 2)
        if average_cost > budget.hotel_cost * 1.15:
            return (
                f"The average recommended stay (₹{average_cost:,.0f} for {days} night(s)) runs above "
                f"your allocated hotel budget of ₹{budget.hotel_cost:,.0f} — consider the budget-tier options above."
            )
        return (
            f"These recommendations fit comfortably within your allocated hotel budget of "
            f"₹{budget.hotel_cost:,.0f} for {days} night(s)."
        )

    @staticmethod
    def _build_booking_tips(request: "TravelRequest", weather: WeatherReport) -> List[str]:
        tips = [
            "Book at least 2-3 weeks in advance for better rates and availability.",
            "Compare weekday vs weekend rates — weekdays are often cheaper.",
        ]
        if weather.season == "monsoon":
            tips.append("Choose refundable bookings during monsoon in case of weather disruptions.")
        if getattr(request.transport_preference, "value", "any") != "car":
            tips.append("Stay near the city center or main attractions if you're not traveling with a car.")
        if request.travelers >= 4:
            tips.append("Look for family/group rooms or serviced apartments for better per-person value.")
        return tips
