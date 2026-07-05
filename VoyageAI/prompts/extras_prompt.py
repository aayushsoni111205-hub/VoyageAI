"""
prompts/extras_prompt.py
--------------------------
Prompt templates for the two smaller report sections - "Things To Do" and
"Local Travel Tips" - both produced by the Itinerary Agent since they share
the same destination knowledge as the day-wise plan.
"""

THINGS_TO_DO_PROMPT_TEMPLATE = """\
List notable things to do for the following trip, beyond what's already in
a day-wise itinerary.

Trip request:
{trip_context}

Give 6-10 bullet points covering sights, experiences, and activities aligned
with the traveler's interests. Prefer variety over repeating the same
category. Keep each bullet to one line.

Respond as plain text using "- " bullet points.
"""

LOCAL_TIPS_PROMPT_TEMPLATE = """\
Give practical local travel tips for the following trip.

Trip request:
{trip_context}

Cover things like local transport options, common scams or etiquette to be
aware of, connectivity/SIM advice, and any cultural norms worth knowing.
Keep it to 5-8 concise bullet points.

Respond as plain text using "- " bullet points.
"""
