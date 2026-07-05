"""
prompts/budget_prompt.py
--------------------------
Prompt template used by the Budget Agent to produce an estimated cost
breakdown that respects the traveler's stated total budget.
"""

BUDGET_PROMPT_TEMPLATE = """\
You are estimating a travel budget breakdown for the following trip.

Trip request:
{trip_context}

Produce a realistic estimated budget breakdown covering: transport,
accommodation, food, activities/entry fees, local transport, and a
miscellaneous/buffer line. Express each line item in the same currency
implied by the budget figure. Make sure the line items roughly sum to the
stated total budget (it's fine to note if the budget is tight or generous
for the trip). End with one sentence of money-saving advice.

Respond as plain text with one line per category, formatted like:
"Transport: ~1200 - round trip bus/train".
"""
