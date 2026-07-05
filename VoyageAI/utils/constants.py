"""
constants.py
------------
Central place for static, non-secret configuration values used across VoyageAI.
Keeping these here avoids magic strings/numbers scattered through the codebase.
"""

APP_NAME: str = "VoyageAI"
APP_TAGLINE: str = "Your Autonomous AI Travel Concierge"

# Gemini model used by every agent unless overridden.
DEFAULT_GEMINI_MODEL: str = "gemini-2.0-flash"

# Interest tags shown as multiselect options in the UI.
INTEREST_OPTIONS: list[str] = [
    "Adventure",
    "Nature",
    "Food",
    "History",
    "Family",
    "Luxury",
    "Beaches",
    "Romantic",
    "Business",
    "Solo",
]

CURRENCY_SYMBOL: str = "₹"

# Bounds used by validators.py
MIN_TRIP_DAYS: int = 1
MAX_TRIP_DAYS: int = 30
MIN_TRAVELERS: int = 1
MAX_TRAVELERS: int = 20
MIN_BUDGET: int = 1000

# Order in which report sections are rendered/exported. Single source of truth
# so the UI and the PDF generator can never drift out of sync.
REPORT_SECTIONS: list[str] = [
    "destination_summary",
    "weather",
    "budget",
    "itinerary",
    "hotels",
    "things_to_do",
    "packing_checklist",
    "local_tips",
]

SECTION_TITLES: dict[str, str] = {
    "destination_summary": "Destination Summary",
    "weather": "Weather",
    "budget": "Estimated Budget",
    "itinerary": "Day-wise Itinerary",
    "hotels": "Hotel Suggestions",
    "things_to_do": "Things To Do",
    "packing_checklist": "Packing Checklist",
    "local_tips": "Local Travel Tips",
}

# Generic, India-focused emergency reference numbers used in the PDF Travel
# Guide's "Travel Tips" section. Not destination-specific (no live directory
# lookup yet) — a reasonable placeholder until a real local-info source is
# integrated.
EMERGENCY_NUMBERS_INDIA: dict[str, str] = {
    "Police": "100",
    "Ambulance": "102 / 108",
    "Fire": "101",
    "Tourist Helpline": "1363",
    "National Emergency Number": "112",
}

GENERAL_SAFETY_TIPS: list[str] = [
    "Share your live location with a trusted contact while traveling.",
    "Keep emergency contacts and hotel address saved offline.",
    "Avoid displaying expensive valuables in crowded public areas.",
    "Use registered taxis or ride-hailing apps after dark.",
]

GENERAL_LOCAL_ETIQUETTE_TIPS: list[str] = [
    "Dress modestly when visiting religious sites.",
    "Ask permission before photographing local people.",
    "Remove footwear where customary (temples, some homes).",
    "Tipping 5-10% is appreciated but not mandatory at most restaurants.",
]

# Static lat/lon lookup for a handful of popular destinations, used to show
# an on-page map without calling a (paid) geocoding API. Destinations not in
# this table fall back to a text-based destination info card in the UI.
DESTINATION_COORDINATES: dict[str, tuple[float, float]] = {
    "goa": (15.2993, 74.1240),
    "manali": (32.2432, 77.1892),
    "jaipur": (26.9124, 75.7873),
    "delhi": (28.6139, 77.2090),
    "mumbai": (19.0760, 72.8777),
    "chennai": (13.0827, 80.2707),
    "kochi": (9.9312, 76.2673),
    "shimla": (31.1048, 77.1734),
    "udaipur": (24.5854, 73.7125),
    "agra": (27.1767, 78.0081),
    "varanasi": (25.3176, 82.9739),
    "rishikesh": (30.0869, 78.2676),
    "leh": (34.1526, 77.5771),
    "pondicherry": (11.9416, 79.8083),
    "darjeeling": (27.0410, 88.2663),
    "ooty": (11.4064, 76.6932),
    "jodhpur": (26.2389, 73.0243),
    "jaisalmer": (26.9157, 70.9083),
    "bengaluru": (12.9716, 77.5946),
    "bangalore": (12.9716, 77.5946),
    "kolkata": (22.5726, 88.3639),
    "hyderabad": (17.3850, 78.4867),
    "pune": (18.5204, 73.8567),
    "ahmedabad": (23.0225, 72.5714),
}
