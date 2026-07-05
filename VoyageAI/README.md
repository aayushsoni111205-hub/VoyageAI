# VoyageAI — Autonomous AI Travel Concierge

VoyageAI is a multi-agent travel planning system. A user submits a trip
request (source city, destination, days, budget, travel dates, interests,
number of travelers) and a **Planner Agent** orchestrates five specialized
sub-agents to assemble a complete trip plan.

## Architecture

```
                      User
                       │
                Streamlit UI (app.py)
                       │
                Planner Agent
                       │
      ┌─────────┬──────────┬───────────┬─────────────┐
      │         │          │           │             │
  Weather    Budget      Hotel     Itinerary       Packing
   Agent      Agent      Agent       Agent           Agent
      │         │          │           │             │
      └─────────┴──────────┴───────────┴─────────────┘
                       │
                 Gemini + Tools
```

Each sub-agent is a small class (`agents/*.py`) that renders a prompt
template (`prompts/*.py`) with the trip context and calls Gemini through a
single shared wrapper (`tools/gemini.py`). The Planner Agent
(`agents/planner.py`) runs all sub-agents concurrently and assembles the
results into one report, which `tools/pdf_generator.py` can export as a PDF.

## Output

For every trip request, VoyageAI generates:

- ✅ Destination summary
- ✅ Weather outlook
- ✅ Estimated budget breakdown
- ✅ Day-wise itinerary
- ✅ Hotel suggestions
- ✅ Things to do
- ✅ Packing checklist
- ✅ Local travel tips
- ✅ Downloadable PDF of the full plan

## Folder structure

```
VoyageAI/
├── app.py                  # Streamlit entrypoint
├── agents/                 # One class per agent + orchestrator
│   ├── base.py
│   ├── planner.py
│   ├── weather.py
│   ├── budget.py
│   ├── hotel.py
│   ├── itinerary.py
│   └── packing.py
├── tools/                  # Shared capabilities agents call into
│   ├── gemini.py
│   ├── pdf_generator.py
│   └── helpers.py
├── skills/                  # Reusable domain-logic modules (see below)
│   ├── weather_skill.py
│   ├── budget_skill.py
│   └── packing_skill.py
├── prompts/                 # Prompt templates, one per agent/section
├── utils/                   # Constants, validators, logger
├── assets/                  # Static assets (images, etc.)
├── docs/                    # Additional documentation
├── requirements.txt
├── .env.example
└── .gitignore
```

## Agent Skills

`agents/*.py` hold orchestration (take a `TravelRequest`, return a structured
report) while `skills/*.py` hold the reusable domain logic behind each
decision — pulled out so multiple agents can share it and so it can be unit
tested without constructing a full `TravelRequest`:

| Skill | Capabilities | Used by |
|---|---|---|
| `skills/weather_skill.py` | weather calculations, clothing recommendations, travel warnings | `agents/weather.py` |
| `skills/budget_skill.py` | expense estimation, budget allocation, remaining budget | `agents/budget.py` |
| `skills/packing_skill.py` | packing checklist, weather-based recommendations, travel reminders | `agents/packing.py` |

**Note on naming:** Google's Agent Development Kit (ADK) has its own,
different `Skill` concept (`google.adk.skills`) — a packaged bundle of
instructions + metadata that an LLM agent discovers and loads at runtime via
a `SkillRegistry`. The `skills/` folder here is a plain Python
software-engineering pattern (reusable function modules), not an ADK
`Skill` object. The name reflects a shared motivation — give an agent a
well-defined, reusable capability instead of one-off inline logic — but the
mechanism is different. If this project adopts real ADK agents later, these
modules could be exposed as ADK tools without changing their internals.

## Installation (Skills addition)

No new dependencies were introduced by this change — `skills/` uses only
the Python standard library. If you're setting up the project fresh:

```bash
pip install -r requirements.txt
```



- Python 3.11+
- Streamlit
- Google Gemini (`google-genai`)
- python-dotenv, requests, pandas, reportlab, Pillow

## Installation

```bash
git clone <your-repo-url>
cd VoyageAI
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env           # then add your GOOGLE_API_KEY
```

## Running locally

```bash
streamlit run app.py
```

Open the URL Streamlit prints (usually `http://localhost:8501`).

## Future roadmap

- Live weather API integration in `WeatherAgent`
- Real hotel-search tool integration (e.g. via an MCP server)
- Multi-turn refinement ("shorten day 2", "make it cheaper")
- Deployment guide (Streamlit Community Cloud / Cloud Run)

## License

MIT — see `LICENSE`.
