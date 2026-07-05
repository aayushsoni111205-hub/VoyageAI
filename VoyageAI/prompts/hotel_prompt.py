"""
prompts/hotel_prompt.py
-------------------------
Prompt template used by the Hotel Agent to suggest accommodation options
across a few budget tiers.
"""

HOTEL_PROMPT_TEMPLATE = """\
Suggest hotel/stay options for the following trip.

Trip request:
{trip_context}

Suggest 3 options spanning budget, mid-range, and premium tiers, each with:
a plausible name/type of stay, the area/neighborhood it's in, an approximate
nightly price consistent with the traveler's total budget, and one line on
why it suits this traveler. Do not claim these are real bookable listings;
frame them as "the kind of stay to look for."

Respond as plain text, one option per paragraph, starting each with the
tier name in brackets, e.g. "[Budget] ...".
"""
