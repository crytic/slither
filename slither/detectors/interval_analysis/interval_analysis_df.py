"""
Interval analysis detection
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from loguru import logger
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


@dataclass(frozen=True)
class FindingKey:
    """Key for interval analysis findings."""

    function_name: str
    variable_name: str
    node_id: Optional[int] = None


@dataclass
class FindingValue:
    """Value for interval analysis findings."""

    interval_ranges: List[Dict[str, str]]
    valid_values: List[str]
    invalid_values: List[str]
    has_overflow: bool
    has_underflow: bool
    var_type: Optional[str] = None


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

    def find_intervals(self) -> Dict[FindingKey, List[FindingValue]]:
        """Find intervals for all functions and return variable ranges."""
        result: Dict[FindingKey, List[FindingValue]] = {}

        for contract in self.contracts:
            for function in contract.functions_and_modifiers_declared:
                if function.is_implemented:
                    logger.info(f"Analyzing function: {function.name}")

                    # Run interval analysis
                    engine = Engine.new(analysis=IntervalAnalysis(), function=function)
                    engine.run_analysis()
                    analysis_results = engine.result()

                    # Extract variable ranges from analysis results
                    function_findings = self._extract_variable_ranges(
                        function.name, analysis_results
                    )
                    result.update(function_findings)

        return result

    def _extract_variable_ranges(
        self, function_name: str, analysis_results: Dict[Node, AnalysisState[IntervalDomain]]
    ) -> Dict[FindingKey, List[FindingValue]]:
        """Extract variable ranges from analysis results."""
        findings: Dict[FindingKey, List[FindingValue]] = {}

        for node, analysis in analysis_results.items():
            if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                continue

            if analysis.post.variant != DomainVariant.STATE:
                continue

            state = analysis.post.state

            # Print node information

            print(f"Node {node.node_id}:", str(node.expression))

            # Get range variables from state
            for var_name, range_var in state.get_range_variables().items():
                if "TMP" in var_name:  # Skip temporary variables
                    continue

                # Extract interval ranges
                interval_ranges: List[Dict[str, str]] = []
                for interval_range in range_var.get_interval_ranges():
                    interval_ranges.append(
                        {
                            "lower": str(interval_range.get_lower()),
                            "upper": str(interval_range.get_upper()),
                        }
                    )

                # Extract valid and invalid values
                valid_values: List[str] = [str(v) for v in range_var.get_valid_values()]
                invalid_values: List[str] = [str(v) for v in range_var.get_invalid_values()]

                # Check for overflow/underflow
                has_overflow: bool = range_var.has_overflow()
                has_underflow: bool = range_var.has_underflow()

                # Create finding key and value
                finding_key = FindingKey(
                    function_name=function_name,
                    variable_name=var_name,
                    node_id=getattr(node, "node_id", None),
                )

                finding_value = FindingValue(
                    interval_ranges=interval_ranges,
                    valid_values=valid_values,
                    invalid_values=invalid_values,
                    has_overflow=has_overflow,
                    has_underflow=has_underflow,
                    var_type=str(range_var.get_var_type()) if range_var.get_var_type() else None,
                )

                # Add to findings
                if finding_key not in findings:
                    findings[finding_key] = []
                findings[finding_key].append(finding_value)

                # Print variable information
                print(f"  Variable: {var_name}")
                print(f"    Type: {range_var.get_var_type()}")

                # Print interval ranges
                if interval_ranges:
                    print(f"    Interval Ranges:")
                    for i, interval in enumerate(interval_ranges):
                        print(f"      [{i}] {interval['lower']} to {interval['upper']}")
                else:
                    print(f"    Interval Ranges: None")

                # Print valid values
                if valid_values:
                    print(f"    Valid Values: {', '.join(valid_values)}")
                else:
                    print(f"    Valid Values: None")

                # Print invalid values
                if invalid_values:
                    print(f"    Invalid Values: {', '.join(invalid_values)}")
                else:
                    print(f"    Invalid Values: None")

                # Print overflow/underflow warnings
                if has_overflow:
                    print(f"    ⚠️ OVERFLOW detected")
                if has_underflow:
                    print(f"    ⚠️ UNDERFLOW detected")

                print()  # Empty line for readability

        return findings

    def _detect(self) -> List[Output]:
        """Main detection method."""
        super()._detect()

        # Run interval analysis to see the logs
        intervals = self.find_intervals()

        # For now, just return empty results
        results: List[Output] = []
        return results
