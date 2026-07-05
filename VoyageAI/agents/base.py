"""
agents/base.py
----------------
Shared base class for all VoyageAI sub-agents. Each specialized agent is
intentionally small: it renders a prompt template with trip context, sends
it to Gemini via tools/gemini.py, and returns plain text. The Planner Agent
owns orchestration (ordering, parallelism, error handling across agents).
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from tools.gemini import generate, GeminiError
from tools.helpers import TripRequest
from utils.logger import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base for a single-purpose travel sub-agent.

    Subclasses implement `build_prompt` to describe *what* to ask Gemini;
    this base class handles *how* the call is made and how failures are
    surfaced so a single agent failing doesn't crash the whole report.
    """

    #: Human-readable name used in logs and error messages.
    name: str = "BaseAgent"

    @abstractmethod
    def build_prompt(self, trip: TripRequest) -> str:
        """Return the fully-rendered prompt for this agent given a trip."""
        raise NotImplementedError

    def run(self, trip: TripRequest) -> str:
        """
        Execute this agent for the given trip request.

        Returns:
            The agent's plain-text output, or a graceful fallback message
            if the underlying Gemini call fails (so the rest of the report
            can still be shown to the user).
        """
        prompt = self.build_prompt(trip)
        try:
            logger.info("Running agent: %s", self.name)
            return generate(prompt)
        except GeminiError as exc:
            logger.error("%s failed: %s", self.name, exc)
            return (
                f"[{self.name} is temporarily unavailable: {exc}]"
            )
