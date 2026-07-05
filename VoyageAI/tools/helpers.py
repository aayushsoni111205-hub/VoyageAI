"""
tools/helpers.py
-----------------
Small, dependency-light utility functions shared across agents and app.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import List


@dataclass
class TripRequest:
    """Structured representation of the user's travel request form."""

    source_city: str
    destination: str
    num_days: int
    budget: float
    travel_start_date: date
    interests: List[str] = field(default_factory=list)
    num_travelers: int = 1

    def to_context_string(self) -> str:
        """
        Render the trip request as plain text for injection into agent prompts.
        Keeping this in one place ensures every agent sees the exact same
        framing of the user's request.
        """
        interests_str = ", ".join(self.interests) if self.interests else "Not specified"
        return (
            f"Source city: {self.source_city}\n"
            f"Destination: {self.destination}\n"
            f"Trip length: {self.num_days} day(s)\n"
            f"Total budget: {self.budget}\n"
            f"Travel start date: {self.travel_start_date.isoformat()}\n"
            f"Interests: {interests_str}\n"
            f"Number of travelers: {self.num_travelers}\n"
        )


def safe_filename(text: str) -> str:
    """Convert arbitrary text into a filesystem-safe filename fragment."""
    keep = (c if c.isalnum() else "_" for c in text.strip())
    cleaned = "".join(keep)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_").lower() or "voyageai_trip"
