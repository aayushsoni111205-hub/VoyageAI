"""
prompts/itinerary_prompt.py
-----------------------------
Prompt template used by the Itinerary Agent to produce a day-wise plan.
"""

ITINERARY_PROMPT_TEMPLATE = """\
Create a day-wise itinerary for the following trip.

Trip request:
{trip_context}

For each day (Day 1 through Day {num_days}), suggest a morning, afternoon,
and evening activity that fits the traveler's interests, keeping travel
between locations realistic for the destination. Weave in local food
suggestions where relevant. Keep pacing reasonable (do not overpack a day).

Respond as plain text formatted like:
"Day 1:
Morning - ...
Afternoon - ...
Evening - ..."
"""
