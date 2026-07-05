"""
prompts/weather_prompt.py
---------------------------
Prompt template used by the Weather Agent. VoyageAI currently uses Gemini's
general knowledge for a seasonal weather outlook rather than a live weather
API call (see tools/gemini.py). Swapping in a live weather API later only
requires changing agents/weather.py, not this prompt contract.
"""

WEATHER_PROMPT_TEMPLATE = """\
Provide a seasonal weather outlook for the following trip.

Trip request:
{trip_context}

Describe the expected temperature range, rainfall/humidity likelihood, and
general conditions for the travel dates given. Add one practical clothing
or timing tip based on the forecast (e.g. "carry a light rain jacket").

Respond in 3-5 plain-text sentences. Do not fabricate a precise forecast;
speak in terms of typical seasonal conditions.
"""
