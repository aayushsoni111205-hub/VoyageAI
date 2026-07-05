"""
validators.py
--------------
Input validation for the trip request form. Keeping validation logic out of
app.py keeps the UI layer thin and makes these rules unit-testable.
"""

from __future__ import annotations

from datetime import date
from typing import List

from utils.constants import (
    MAX_TRIP_DAYS,
    MIN_BUDGET,
    MIN_TRAVELERS,
    MAX_TRAVELERS,
    MIN_TRIP_DAYS,
)


class ValidationError(Exception):
    """Raised when a TripRequest fails validation."""


def validate_trip_request(
    source_city: str,
    destination: str,
    num_days: int,
    budget: float,
    travel_start_date: date,
    interests: List[str],
    num_travelers: int,
) -> None:
    """
    Validate raw form input for a trip request.

    Raises:
        ValidationError: with a human-readable message describing the first
        problem found.
    """
    if not source_city or not source_city.strip():
        raise ValidationError("Source city is required.")

    if not destination or not destination.strip():
        raise ValidationError("Destination is required.")

    if source_city.strip().lower() == destination.strip().lower():
        raise ValidationError("Source city and destination cannot be the same.")

    if not (MIN_TRIP_DAYS <= num_days <= MAX_TRIP_DAYS):
        raise ValidationError(
            f"Number of days must be between {MIN_TRIP_DAYS} and {MAX_TRIP_DAYS}."
        )

    if budget < MIN_BUDGET:
        raise ValidationError(f"Budget must be at least {MIN_BUDGET}.")

    if travel_start_date < date.today():
        raise ValidationError("Travel start date cannot be in the past.")

    if not interests:
        raise ValidationError("Select at least one interest.")

    if not (MIN_TRAVELERS <= num_travelers <= MAX_TRAVELERS):
        raise ValidationError(
            f"Number of travelers must be between {MIN_TRAVELERS} and {MAX_TRAVELERS}."
        )
