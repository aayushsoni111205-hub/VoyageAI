"""
tools/pdf_generator.py
-----------------------
Day 2 Afternoon — Professional multi-page PDF Travel Guide generator.

Public contract:
    TravelPDFGenerator().generate_travel_pdf(plan, request) -> bytes

Turns a fully-assembled TravelPlan + TravelRequest into a portfolio-quality
PDF (cover page, trip summary, weather, budget, hotels, day-wise itinerary,
packing checklist, travel tips, and a running footer). Built entirely with
reportlab — no external services — so it works today and continues to work
once Gemini-backed agents replace today's mock data (the PDF only depends
on the TravelPlan/TravelRequest contracts, not on how their fields were
produced).

NOTE: currency amounts are rendered as "Rs. X" rather than "₹X" inside the
PDF. ReportLab's built-in base-14 fonts do not include the ₹ glyph, which
renders as a solid black box — "Rs." is the safe, portable choice for a
generated PDF.
"""

from __future__ import annotations

import io
from datetime import datetime, timedelta
from typing import List, Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    ListFlowable,
    ListItem,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from agents.planner import TravelPlan, TravelRequest
from utils.constants import (
    EMERGENCY_NUMBERS_INDIA,
    GENERAL_LOCAL_ETIQUETTE_TIPS,
    GENERAL_SAFETY_TIPS,
)
from utils.logger import get_logger

logger = get_logger(__name__)

_BRAND_COLOR = colors.HexColor("#1f4e79")
_ACCENT_COLOR = colors.HexColor("#2e86ab")
_LIGHT_GREY = colors.HexColor("#f2f2f2")


class PDFGenerationError(RuntimeError):
    """Raised when the Travel Guide PDF cannot be generated."""


def _format_money(amount: float) -> str:
    """Render a currency amount without the ₹ glyph (see module docstring)."""
    return f"Rs. {amount:,.0f}"


class TravelPDFGenerator:
    """Builds the VoyageAI PDF Travel Guide from a completed TravelPlan."""

    def __init__(self) -> None:
        base_styles = getSampleStyleSheet()
        self.styles = base_styles
        self.styles.add(ParagraphStyle(
            "VoyageCoverTitle", parent=base_styles["Title"], fontSize=30,
            textColor=_BRAND_COLOR, alignment=TA_CENTER, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageCoverSubtitle", parent=base_styles["Normal"], fontSize=14,
            textColor=_ACCENT_COLOR, alignment=TA_CENTER, spaceAfter=4,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageSectionHeading", parent=base_styles["Heading1"], fontSize=17,
            textColor=_BRAND_COLOR, spaceBefore=6, spaceAfter=10,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageSubHeading", parent=base_styles["Heading2"], fontSize=13,
            textColor=_ACCENT_COLOR, spaceBefore=10, spaceAfter=6,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageBody", parent=base_styles["BodyText"], fontSize=10.5, leading=15,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageMuted", parent=base_styles["Normal"], fontSize=9,
            textColor=colors.grey, alignment=TA_CENTER,
        ))
        self.styles.add(ParagraphStyle(
            "VoyageWarning", parent=base_styles["BodyText"], fontSize=10.5,
            textColor=colors.HexColor("#a94442"), leading=15,
        ))

    # ------------------------------------------------------------
    # Public entrypoint
    # ------------------------------------------------------------
    def generate_travel_pdf(self, plan: TravelPlan, request: TravelRequest) -> bytes:
        """
        Build the complete Travel Guide PDF.

        Args:
            plan: The Planner Agent's assembled TravelPlan.
            request: The original TravelRequest (used for the cover page and
                trip summary).

        Returns:
            Raw PDF bytes, ready for st.download_button.

        Raises:
            PDFGenerationError: if the document cannot be built.
        """
        try:
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(
                buffer,
                pagesize=A4,
                leftMargin=2 * cm,
                rightMargin=2 * cm,
                topMargin=2 * cm,
                bottomMargin=2.2 * cm,
                title=f"VoyageAI Travel Guide - {request.destination}",
            )

            story: List = []
            self._build_cover_page(story, plan, request)
            self._build_trip_summary(story, request)
            self._build_weather_section(story, plan)
            self._build_budget_section(story, plan)
            self._build_hotel_section(story, plan)
            self._build_itinerary_section(story, plan)
            self._build_packing_section(story, plan)
            self._build_travel_tips_section(story, plan)

            doc.build(
                story,
                onFirstPage=self._draw_footer,
                onLaterPages=self._draw_footer,
            )
            return buffer.getvalue()
        except Exception as exc:  # noqa: BLE001 - surface as a single, clear error type
            logger.error("PDF generation failed: %s", exc)
            raise PDFGenerationError(f"Could not generate the Travel Guide PDF: {exc}") from exc

    # ------------------------------------------------------------
    # Footer (drawn on every page)
    # ------------------------------------------------------------
    @staticmethod
    def _draw_footer(canvas, doc) -> None:
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(2 * cm, 1.2 * cm, "VoyageAI | Generated by AI Travel Concierge")
        canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {doc.page}")
        canvas.restoreState()

    # ------------------------------------------------------------
    # Section builders
    # ------------------------------------------------------------
    def _build_cover_page(self, story: List, plan: TravelPlan, request: TravelRequest) -> None:
        end_date = request.travel_dates + timedelta(days=max(request.days - 1, 0))

        story.append(Spacer(1, 3 * cm))
        story.append(Paragraph("VoyageAI", self.styles["VoyageCoverTitle"]))
        story.append(Paragraph("AI Travel Concierge", self.styles["VoyageCoverSubtitle"]))
        story.append(Spacer(1, 1.5 * cm))
        story.append(HRFlowable(width="60%", color=_ACCENT_COLOR, thickness=1, hAlign="CENTER"))
        story.append(Spacer(1, 0.8 * cm))
        story.append(Paragraph(
            f"{request.source_city} -&gt; {request.destination}",
            ParagraphStyle("CoverTripTitle", parent=self.styles["Title"], fontSize=22, alignment=TA_CENTER),
        ))
        story.append(Paragraph(
            f"{request.travel_dates.isoformat()} to {end_date.isoformat()} "
            f"| {request.days} day(s)",
            self.styles["VoyageCoverSubtitle"],
        ))
        story.append(Spacer(1, 2 * cm))
        story.append(Paragraph(
            f"Generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}",
            self.styles["VoyageMuted"],
        ))
        story.append(PageBreak())

    def _build_trip_summary(self, story: List, request: TravelRequest) -> None:
        story.append(Paragraph("Trip Summary", self.styles["VoyageSectionHeading"]))

        rows = [
            ["Source", request.source_city],
            ["Destination", request.destination],
            ["Travelers", str(request.travelers)],
            ["Budget", _format_money(request.budget)],
            ["Hotel Preference", getattr(request.hotel_preference, "value", "any").replace("_", " ").title()],
            ["Transport Preference", getattr(request.transport_preference, "value", "any").title()],
            ["Interests", ", ".join(request.interests) if request.interests else "Not specified"],
        ]
        story.append(self._make_table(rows, col_widths=[4.5 * cm, 11 * cm]))
        story.append(Spacer(1, 0.6 * cm))

    def _build_weather_section(self, story: List, plan: TravelPlan) -> None:
        weather = plan.weather
        if not weather:
            return

        story.append(Paragraph("Weather Report", self.styles["VoyageSectionHeading"]))
        rows = [
            ["Temperature", f"{weather.temperature_celsius}\u00b0C"],
            ["Condition", weather.weather_condition],
            ["Humidity", f"{weather.humidity_percent}%"],
            ["Rain Chance", f"{weather.rain_probability_percent}%"],
            ["Wind Speed", f"{weather.wind_speed_kmph} km/h"],
            ["UV Index", str(weather.uv_index)],
            ["Recommended Clothing", weather.recommended_clothing],
        ]
        story.append(self._make_table(rows, col_widths=[4.5 * cm, 11 * cm]))

        if weather.packing_suggestions:
            story.append(Paragraph("Packing Suggestions", self.styles["VoyageSubHeading"]))
            story.append(self._make_bullet_list(weather.packing_suggestions))

        if weather.travel_warning:
            story.append(Spacer(1, 0.2 * cm))
            story.append(Paragraph(f"Warning: {weather.travel_warning}", self.styles["VoyageWarning"]))

        story.append(Spacer(1, 0.6 * cm))

    def _build_budget_section(self, story: List, plan: TravelPlan) -> None:
        budget = plan.estimated_budget
        if not budget:
            return

        story.append(Paragraph("Budget Report", self.styles["VoyageSectionHeading"]))
        summary_rows = [
            ["Total Budget", _format_money(budget.total_budget)],
            ["Estimated Cost", _format_money(budget.total_estimated_cost)],
            ["Remaining Budget", _format_money(budget.remaining_budget)],
        ]
        story.append(self._make_table(summary_rows, col_widths=[4.5 * cm, 11 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("Budget Breakdown", self.styles["VoyageSubHeading"]))
        breakdown_rows = [["Category", "Amount"]] + [
            [category, _format_money(amount)] for category, amount in budget.as_breakdown_dict().items()
        ]
        story.append(self._make_table(breakdown_rows, col_widths=[8 * cm, 7 * cm], header=True))
        story.append(Spacer(1, 0.2 * cm))
        story.append(Paragraph(budget.notes, self.styles["VoyageBody"]))
        story.append(Spacer(1, 0.6 * cm))

    def _build_hotel_section(self, story: List, plan: TravelPlan) -> None:
        hotel_report = plan.hotel_recommendations
        if not hotel_report:
            return

        story.append(Paragraph("Hotel Recommendations", self.styles["VoyageSectionHeading"]))
        for hotel in hotel_report.recommended_hotels:
            is_best_value = hotel.hotel_name == hotel_report.best_value_hotel.hotel_name
            title = hotel.hotel_name + ("  (Best Value)" if is_best_value else "")
            story.append(Paragraph(title, self.styles["VoyageSubHeading"]))

            rows = [
                ["Category", hotel.hotel_category],
                ["Price / Night", _format_money(hotel.price_per_night)],
                ["Rating", f"{hotel.rating} / 5.0"],
                ["Amenities", ", ".join(hotel.amenities)],
                ["Best For", hotel.best_for],
            ]
            story.append(self._make_table(rows, col_widths=[4.5 * cm, 11 * cm]))
            story.append(Paragraph(hotel.short_description, self.styles["VoyageBody"]))
            story.append(Spacer(1, 0.3 * cm))

        if hotel_report.booking_tips:
            story.append(Paragraph("Booking Tips", self.styles["VoyageSubHeading"]))
            story.append(self._make_bullet_list(hotel_report.booking_tips))

        story.append(Spacer(1, 0.4 * cm))

    def _build_itinerary_section(self, story: List, plan: TravelPlan) -> None:
        itinerary = plan.daywise_itinerary
        if not itinerary:
            return

        story.append(PageBreak())
        story.append(Paragraph("Day-wise Itinerary", self.styles["VoyageSectionHeading"]))
        if itinerary.overview:
            story.append(Paragraph(itinerary.overview, self.styles["VoyageBody"]))
            story.append(Spacer(1, 0.3 * cm))

        for day_plan in itinerary.daily_plans:
            story.append(Paragraph(f"Day {day_plan.day_number}", self.styles["VoyageSubHeading"]))
            rows = [
                ["Morning", f"{day_plan.breakfast}. {day_plan.morning_activity}."],
                ["Afternoon", f"{day_plan.lunch}. {day_plan.afternoon_activity}."],
                ["Evening", day_plan.evening_activity + "."],
                ["Night", day_plan.dinner + "."],
            ]
            story.append(self._make_table(rows, col_widths=[3 * cm, 12.5 * cm]))
            story.append(Spacer(1, 0.3 * cm))

    def _build_packing_section(self, story: List, plan: TravelPlan) -> None:
        packing = plan.packing_list
        if not packing:
            return

        story.append(PageBreak())
        story.append(Paragraph("Packing Checklist", self.styles["VoyageSectionHeading"]))

        categories = [
            ("Documents", packing.travel_documents),
            ("Electronics", packing.electronics),
            ("Clothing", packing.clothing),
            ("Footwear", packing.footwear),
            ("Medical", packing.medical),
            ("Toiletries", packing.toiletries),
            ("Weather Essentials", packing.weather_essentials),
            ("Adventure Gear", packing.adventure_gear),
            ("Food & Snacks", packing.food_snacks),
            ("Miscellaneous", packing.miscellaneous),
        ]
        for label, items in categories:
            if not items:
                continue
            story.append(Paragraph(label, self.styles["VoyageSubHeading"]))
            story.append(self._make_bullet_list(items))

        story.append(Spacer(1, 0.5 * cm))

    def _build_travel_tips_section(self, story: List, plan: TravelPlan) -> None:
        story.append(PageBreak())
        story.append(Paragraph("Travel Tips", self.styles["VoyageSectionHeading"]))

        story.append(Paragraph("Emergency Numbers", self.styles["VoyageSubHeading"]))
        emergency_rows = [[name, number] for name, number in EMERGENCY_NUMBERS_INDIA.items()]
        story.append(self._make_table(emergency_rows, col_widths=[7 * cm, 8 * cm]))
        story.append(Spacer(1, 0.3 * cm))

        story.append(Paragraph("Safety Tips", self.styles["VoyageSubHeading"]))
        story.append(self._make_bullet_list(GENERAL_SAFETY_TIPS))

        story.append(Paragraph("Local Etiquette", self.styles["VoyageSubHeading"]))
        story.append(self._make_bullet_list(GENERAL_LOCAL_ETIQUETTE_TIPS))

        if plan.travel_tips:
            story.append(Paragraph("Useful Advice", self.styles["VoyageSubHeading"]))
            story.append(self._make_bullet_list(plan.travel_tips))

    # ------------------------------------------------------------
    # Small reportlab builders shared across sections
    # ------------------------------------------------------------
    def _make_table(self, rows: List[List[str]], col_widths: List[float], header: bool = False) -> Table:
        wrapped_rows = [
            [Paragraph(str(cell), self.styles["VoyageBody"]) for cell in row] for row in rows
        ]
        table = Table(wrapped_rows, colWidths=col_widths, hAlign="LEFT")

        style_commands = [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
        if header:
            style_commands.append(("BACKGROUND", (0, 0), (-1, 0), _BRAND_COLOR))
            style_commands.append(("TEXTCOLOR", (0, 0), (-1, 0), colors.white))
        else:
            style_commands.append(("BACKGROUND", (0, 0), (0, -1), _LIGHT_GREY))

        table.setStyle(TableStyle(style_commands))
        return table

    def _make_bullet_list(self, items: List[str]) -> ListFlowable:
        return ListFlowable(
            [ListItem(Paragraph(item, self.styles["VoyageBody"]), leftIndent=6) for item in items],
            bulletType="bullet",
            start="circle",
            leftIndent=14,
        )
