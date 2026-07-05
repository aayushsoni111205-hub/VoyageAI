"""
app.py
------
Day 2 Afternoon/Evening — Polished Streamlit UI for VoyageAI.

No business-logic changes here: this file is purely presentation. It
collects a TravelRequest, hands it to the Planner Agent (unchanged), and
renders the resulting TravelPlan as a modern, card-based travel app with a
downloadable PDF Travel Guide.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st
from datetime import date, timedelta

from agents.planner import (
    HotelPreference,
    PlannerAgent,
    TransportPreference,
    TravelPlan,
    TravelRequest,
    TravelRequestValidationError,
)
from tools.helpers import safe_filename
from tools.pdf_generator import PDFGenerationError, TravelPDFGenerator
from utils.constants import APP_NAME, APP_TAGLINE, DESTINATION_COORDINATES, INTEREST_OPTIONS

st.set_page_config(
    page_title=f"{APP_NAME} | {APP_TAGLINE}",
    page_icon="🧭",
    layout="wide",
)

# --------------------------------------------------------------------------
# Light custom styling (kept minimal and purely cosmetic)
# --------------------------------------------------------------------------
st.markdown(
    """
    <style>
        .voyage-hero {
            padding: 1.6rem 2rem;
            border-radius: 14px;
            background: linear-gradient(135deg, #1f4e79 0%, #2e86ab 100%);
            color: white;
            margin-bottom: 1.2rem;
        }
        .voyage-hero h1 { margin-bottom: 0.1rem; }
        .voyage-hero p { margin-top: 0; opacity: 0.9; }
        div[data-testid="stMetricValue"] { font-size: 1.4rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Hero banner
# --------------------------------------------------------------------------
st.markdown(
    f"""
    <div class="voyage-hero">
        <h1>🧭 {APP_NAME}</h1>
        <p>{APP_TAGLINE} — orchestrated by a Planner Agent across Weather, Budget,
        Hotel, Itinerary, and Packing specialists.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# --------------------------------------------------------------------------
# Sidebar: branding, description, trip request form
# --------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🧭 VoyageAI")
    st.caption("Plan a full trip in seconds — weather, budget, hotels, itinerary, and packing, all in one place.")
    st.divider()

    with st.form("trip_request_form"):
        st.subheader("Plan your trip")

        source_city = st.text_input("Source city", placeholder="Ahmedabad")
        destination = st.text_input("Destination", placeholder="Goa")
        travel_dates = st.date_input("Travel start date", value=date.today() + timedelta(days=14))
        days = st.number_input("Number of days", min_value=1, max_value=30, value=5)
        travelers = st.number_input("Number of travelers", min_value=1, max_value=20, value=2)
        budget = st.number_input("Budget (₹)", min_value=1000.0, value=35000.0, step=1000.0)
        interests = st.multiselect("Travel interests", options=INTEREST_OPTIONS, default=["Adventure", "Beaches"])
        transport_preference = st.selectbox(
            "Transport preference", options=list(TransportPreference),
            format_func=lambda o: o.value.replace("_", " ").title(),
        )
        hotel_preference = st.selectbox(
            "Hotel preference", options=list(HotelPreference),
            format_func=lambda o: o.value.replace("_", " ").title(),
        )
        special_requirements = st.text_area(
            "Special requirements (optional)",
            placeholder="e.g. 'I only need a packing list' or leave blank for a full plan",
        )

        col_generate, col_reset = st.columns(2)
        generate_clicked = col_generate.form_submit_button("✨ Generate Plan", width="stretch", type="primary")
        reset_clicked = col_reset.form_submit_button("🔄 Reset", width="stretch")

    st.divider()
    st.caption(f"{APP_NAME} — built for the Kaggle AI Agents Intensive Capstone.")

# --------------------------------------------------------------------------
# Handle Reset
# --------------------------------------------------------------------------
if reset_clicked:
    st.session_state.clear()
    st.rerun()

# --------------------------------------------------------------------------
# Handle Generate
# --------------------------------------------------------------------------
if generate_clicked:
    request = TravelRequest(
        source_city=source_city.strip(),
        destination=destination.strip(),
        travel_dates=travel_dates,
        days=int(days),
        budget=float(budget),
        travelers=int(travelers),
        interests=interests,
        transport_preference=transport_preference,
        hotel_preference=hotel_preference,
        special_requirements=special_requirements or None,
    )

    planner = PlannerAgent()
    try:
        with st.spinner("VoyageAI's agents are planning your trip..."):
            plan = planner.generate_travel_plan(request)
        st.session_state["travel_plan"] = plan
        st.session_state["travel_request"] = request
        st.session_state.pop("pdf_bytes", None)  # invalidate any previously generated PDF
    except TravelRequestValidationError as exc:
        st.error(f"Please fix your request: {exc}")

# --------------------------------------------------------------------------
# Card renderers
# --------------------------------------------------------------------------
def _render_summary_card(request: TravelRequest) -> None:
    with st.container(border=True):
        st.subheader("📋 Travel Summary")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Destination", request.destination)
        col2.metric("Duration", f"{request.days} day(s)")
        col3.metric("Travelers", request.travelers)
        col4.metric("Budget", f"₹{request.budget:,.0f}")
        st.caption(
            f"From {request.source_city} · Starting {request.travel_dates.isoformat()} · "
            f"Interests: {', '.join(request.interests) if request.interests else 'Not specified'}"
        )


def _render_weather_card(weather) -> None:
    with st.container(border=True):
        st.subheader("🌤️ Weather")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Temperature", f"{weather.temperature_celsius}°C")
        col2.metric("Rain Chance", f"{weather.rain_probability_percent}%")
        col3.metric("Humidity", f"{weather.humidity_percent}%")
        col4.metric("Wind", f"{weather.wind_speed_kmph} km/h")
        col5.metric("UV Index", weather.uv_index)

        st.write(f"**Condition:** {weather.weather_condition}")
        st.write(f"**Recommended clothing:** {weather.recommended_clothing}")

        with st.expander("Packing suggestions"):
            for item in weather.packing_suggestions:
                st.write(f"- {item}")

        if weather.travel_warning:
            st.warning(weather.travel_warning)


def _render_budget_card(budget) -> None:
    with st.container(border=True):
        st.subheader("💰 Budget")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Budget", f"₹{budget.total_budget:,.0f}")
        col2.metric("Estimated Cost", f"₹{budget.total_estimated_cost:,.0f}")
        col3.metric("Remaining", f"₹{budget.remaining_budget:,.0f}")

        if budget.is_over_budget:
            st.warning("This plan is estimated to exceed your stated budget.")
        else:
            st.success("This plan fits comfortably within your stated budget.")

        breakdown_df = pd.DataFrame(
            list(budget.as_breakdown_dict().items()), columns=["Category", "Amount (₹)"]
        )
        col_table, col_chart = st.columns([1, 1])
        with col_table:
            st.dataframe(breakdown_df, hide_index=True, width="stretch")
        with col_chart:
            st.bar_chart(breakdown_df.set_index("Category"))

        st.caption(budget.notes)


def _render_hotel_card(hotel_report) -> None:
    with st.container(border=True):
        st.subheader("🏨 Hotel Recommendations")
        best_name = hotel_report.best_value_hotel.hotel_name
        cols = st.columns(2)
        for index, hotel in enumerate(hotel_report.recommended_hotels):
            with cols[index % 2]:
                badge = " 🏆 Best Value" if hotel.hotel_name == best_name else ""
                with st.container(border=True):
                    st.markdown(f"**{hotel.hotel_name}**{badge}")
                    st.caption(f"{hotel.hotel_category} · {hotel.distance_from_city_center} from city center")
                    st.write(f"⭐ {hotel.rating} rating")
                    st.write(f"₹{hotel.price_per_night:,.0f}/night (≈ ₹{hotel.estimated_total_cost:,.0f} total)")
                    st.write(f"**Best for:** {hotel.best_for}")
                    st.write(hotel.short_description)
                    st.write("**Amenities:** " + ", ".join(hotel.amenities))

        st.info(hotel_report.budget_summary)
        with st.expander("Booking tips"):
            for tip in hotel_report.booking_tips:
                st.write(f"- {tip}")


def _render_itinerary_card(itinerary) -> None:
    with st.container(border=True):
        st.subheader("🗺️ Day-wise Itinerary")
        st.write(itinerary.overview)
        for day_plan in itinerary.daily_plans:
            with st.expander(f"Day {day_plan.day_number}"):
                st.write(f"🍳 **Breakfast:** {day_plan.breakfast}")
                st.write(f"🌅 **Morning:** {day_plan.morning_activity}")
                st.write(f"🍽️ **Lunch:** {day_plan.lunch}")
                st.write(f"☀️ **Afternoon:** {day_plan.afternoon_activity}")
                st.write(f"🌆 **Evening:** {day_plan.evening_activity}")
                st.write(f"🍴 **Dinner:** {day_plan.dinner}")


def _render_packing_card(packing) -> None:
    with st.container(border=True):
        st.subheader("🎒 Packing Checklist")
        sections = [
            ("📄 Documents", packing.travel_documents),
            ("🔌 Electronics", packing.electronics),
            ("👕 Clothing", packing.clothing),
            ("👟 Footwear", packing.footwear),
            ("💊 Medical", packing.medical),
            ("🧴 Toiletries", packing.toiletries),
            ("🌦️ Weather Essentials", packing.weather_essentials),
            ("🧗 Adventure Gear", packing.adventure_gear),
            ("🍫 Food & Snacks", packing.food_snacks),
            ("📦 Miscellaneous", packing.miscellaneous),
        ]
        col1, col2 = st.columns(2)
        for index, (label, items) in enumerate(sections):
            if not items:
                continue
            with (col1 if index % 2 == 0 else col2):
                with st.expander(label, expanded=True):
                    for item in items:
                        st.checkbox(item, key=f"pack_{label}_{item}")

        if packing.travel_reminders:
            with st.expander("💡 Travel Reminders", expanded=True):
                for reminder in packing.travel_reminders:
                    st.write(f"- {reminder.message}")


def _render_travel_tips_card(plan: TravelPlan) -> None:
    with st.container(border=True):
        st.subheader("💡 Travel Tips")
        if plan.travel_tips:
            for tip in plan.travel_tips:
                st.write(f"- {tip}")
        else:
            st.caption("No additional travel tips were requested for this plan.")


def _render_destination_card(request: TravelRequest, plan: TravelPlan) -> None:
    with st.container(border=True):
        st.subheader("📍 Destination")
        coords = DESTINATION_COORDINATES.get(request.destination.strip().lower())
        if coords:
            map_df = pd.DataFrame([{"lat": coords[0], "lon": coords[1]}])
            st.map(map_df, zoom=8, width="stretch")
        else:
            st.info("A map preview isn't available for this destination yet — here's a quick overview instead.")
        if plan.destination_summary:
            st.write(plan.destination_summary)


# --------------------------------------------------------------------------
# Main render
# --------------------------------------------------------------------------
if "travel_plan" in st.session_state:
    plan: TravelPlan = st.session_state["travel_plan"]
    request: TravelRequest = st.session_state["travel_request"]

    st.success(f"Travel plan ready: {request.source_city} → {request.destination}")

    _render_summary_card(request)
    st.write("")

    if plan.destination_summary or DESTINATION_COORDINATES.get(request.destination.strip().lower()):
        _render_destination_card(request, plan)
        st.write("")

    if plan.weather:
        _render_weather_card(plan.weather)
        st.write("")

    if plan.estimated_budget:
        _render_budget_card(plan.estimated_budget)
        st.write("")

    if plan.hotel_recommendations:
        _render_hotel_card(plan.hotel_recommendations)
        st.write("")

    if plan.daywise_itinerary:
        _render_itinerary_card(plan.daywise_itinerary)
        st.write("")

    if plan.packing_list:
        _render_packing_card(plan.packing_list)
        st.write("")

    if plan.travel_tips:
        _render_travel_tips_card(plan)
        st.write("")

    # ----------------------------------------------------------------
    # PDF download
    # ----------------------------------------------------------------
    st.divider()
    st.subheader("📄 Download your Travel Guide")
    try:
        if "pdf_bytes" not in st.session_state:
            with st.spinner("Preparing your PDF Travel Guide..."):
                st.session_state["pdf_bytes"] = TravelPDFGenerator().generate_travel_pdf(plan, request)
        st.download_button(
            label="Download PDF Travel Guide",
            data=st.session_state["pdf_bytes"],
            file_name=f"voyageai_{safe_filename(request.destination)}_travel_guide.pdf",
            mime="application/pdf",
            width="stretch",
        )
    except PDFGenerationError as exc:
        st.error(f"Couldn't generate the PDF right now: {exc}")

else:
    st.info("Fill in the sidebar and click **✨ Generate Plan** to get started.")

# --------------------------------------------------------------------------
# Footer
# --------------------------------------------------------------------------
st.divider()
st.caption(f"{APP_NAME} · {APP_TAGLINE} · Built for the Kaggle AI Agents Intensive Capstone")
