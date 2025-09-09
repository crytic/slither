"""
Interval analysis detection
"""

from collections import defaultdict, namedtuple
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import IntervalDomain
from slither.analyses.data_flow.engine.engine import Engine
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification

from slither.utils.output import Output


@dataclass
class FindingKey:
    attr1: Optional[Any] = None


@dataclass
class FindingValue:
    attr1: Optional[Any] = None


class IntervalAnalysisDF(AbstractDetector):
    ARGUMENT = "interval-analysis-df"
    HELP = "Interval analysis detection"
    IMPACT = DetectorClassification.HIGH
    CONFIDENCE = DetectorClassification.MEDIUM
    WIKI = "tbd"
    WIKI_TITLE = "tbd"
    WIKI_DESCRIPTION = "tbd"
    WIKI_EXPLOIT_SCENARIO = "tbd"
    WIKI_RECOMMENDATION = "tbd"
    STANDARD_JSON = False

    def find_intervals(self) -> Dict[FindingKey, Set[FindingValue]]:
        result: Dict[FindingKey, Set[FindingValue]] = {}

        return result

    def _detect(self) -> List[Output]:
        super()._detect()
        results: List[Output] = []
        return results
