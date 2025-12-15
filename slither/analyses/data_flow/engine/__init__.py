"""Data flow analysis engine."""

from .analysis import Analysis, AnalysisState
from .direction import Direction
from .domain import Domain
from .engine import Engine

# InterproceduralAnalyzer is not imported here to avoid circular imports.
# Import directly: from slither.analyses.data_flow.engine.interprocedural import InterproceduralAnalyzer

__all__ = [
    "Analysis",
    "AnalysisState",
    "Direction",
    "Domain",
    "Engine",
]

