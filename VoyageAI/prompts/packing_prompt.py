"""
prompts/packing_prompt.py
---------------------------
Prompt template used by the Packing Agent to produce a checklist tailored
to destination climate, trip length, and interests.
"""

PACKING_PROMPT_TEMPLATE = """\
Create a packing checklist for the following trip.

Trip request:
{trip_context}

Tailor the list to the destination's likely climate/season, the trip length,
and the traveler's interests (e.g. add trekking gear for Adventure, formal
wear for Luxury, sunscreen/swimwear for Beaches). Group items under short
category labels (Clothing, Essentials, Health & Safety, Interest-specific).

Respond as plain text using "- " bullet points, grouped under category
labels written as short lines ending in ":".
"""
