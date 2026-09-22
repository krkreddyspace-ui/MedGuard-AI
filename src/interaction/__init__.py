"""Interaction matching package."""
from .engine import InteractionEngine, get_interaction_engine
from .models import InteractionResult, InteractionStatus, SeverityLevel

__all__ = [
    "InteractionEngine",
    "InteractionResult",
    "InteractionStatus",
    "SeverityLevel",
    "get_interaction_engine",
]
