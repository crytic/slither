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
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.declarations.function import Function
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output


@dataclass(frozen=True)
class FindingKey:
    """Key for interval analysis findings."""

    function: Function
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
    variable_name: Optional[str] = None


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
                if not function.is_implemented or function.is_constructor:
                    continue

                # Run interval analysis
                engine = Engine.new(analysis=IntervalAnalysis(), function=function)
                engine.run_analysis()
                analysis_results = engine.result()

                # Extract variable ranges from analysis results
                function_findings = self._extract_variable_ranges(function, analysis_results)
                result.update(function_findings)

        return result

    def _extract_variable_ranges(
        self, function, analysis_results: Dict[Node, AnalysisState[IntervalDomain]]
    ) -> Dict[FindingKey, List[FindingValue]]:
        """Extract variable ranges from analysis results."""
        findings: Dict[FindingKey, List[FindingValue]] = {}

        for node, analysis in analysis_results.items():
            if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                continue

            if analysis.post.variant != DomainVariant.STATE:
                continue

            state = analysis.post.state

            # Get range variables from state
            for var_name, range_var in state.get_range_variables().items():
                # Skip boolean variables
                if range_var.get_var_type() == ElementaryType("bool"):
                    continue

                # Check for overflow/underflow first
                has_overflow: bool = range_var.has_overflow()
                has_underflow: bool = range_var.has_underflow()

                # Only include variables that have overflow/underflow issues
                if not (has_overflow or has_underflow):
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

                # Create finding key and value
                finding_key = FindingKey(
                    function=function,
                    variable_name=var_name,
                    node_id=node.node_id,
                )

                finding_value = FindingValue(
                    interval_ranges=interval_ranges,
                    valid_values=valid_values,
                    invalid_values=invalid_values,
                    has_overflow=has_overflow,
                    has_underflow=has_underflow,
                    var_type=str(range_var.get_var_type()) if range_var.get_var_type() else None,
                    variable_name=var_name,
                )

                # Add to findings
                if finding_key not in findings:
                    findings[finding_key] = []
                findings[finding_key].append(finding_value)

        return findings

    def _detect(self) -> List[Output]:
        """Main detection method."""
        super()._detect()
        intervals = self.find_intervals()
        results: List[Output] = []

        # Sort findings by function name for consistent output
        result_sorted = sorted(list(intervals.items()), key=lambda x: x[0].function.name)

        for finding_key, finding_values in result_sorted:
            # Build info string for this finding
            info = [
                f"Interval analysis for variable '{finding_key.variable_name}' in function '{finding_key.function.name}':\n"
            ]

            for finding_value in finding_values:
                # Add node information
                if finding_key.node_id is not None:
                    info += [f"\tNode {finding_key.node_id}"]
                    # Find the node to get its expression
                    node = next(
                        (n for n in finding_key.function.nodes if n.node_id == finding_key.node_id),
                        None,
                    )
                    if node and hasattr(node, "expression") and node.expression:
                        info += [f": {node.expression}\n"]
                    else:
                        info += ["\n"]
                # Add variable type information first
                if finding_value.var_type:
                    info += [f"\tType: {finding_value.var_type}\n"]

                # Add overflow/underflow warnings prominently
                warnings = []
                if finding_value.has_overflow:
                    warnings.append("OVERFLOW")
                if finding_value.has_underflow:
                    warnings.append("UNDERFLOW")

                if warnings:
                    info += [f"\t⚠️  WARNINGS: {', '.join(warnings)}\n"]

                # Add interval ranges information
                if finding_value.interval_ranges:
                    info += ["\tRanges: "]
                    range_strs = []
                    for interval in finding_value.interval_ranges:
                        range_strs.append(f"[{interval['lower']}, {interval['upper']}]")
                    info += [f"{', '.join(range_strs)}\n"]
                else:
                    info += ["\tRanges: None\n"]

                # Add valid values information
                if finding_value.valid_values:
                    info += [f"\tValid: {', '.join(finding_value.valid_values)}\n"]
                else:
                    info += ["\tValid: None\n"]

                # Add invalid values information
                if finding_value.invalid_values:
                    info += [f"\tInvalid: {', '.join(finding_value.invalid_values)}\n"]
                else:
                    info += ["\tInvalid: None\n"]

            # Generate result and add nodes
            res = self.generate_result(info)

            # Add the function to the result
            res.add(finding_key.function)

            # Add nodes with metadata
            for finding_value in finding_values:
                # Find the node by node_id
                node = None
                if finding_key.node_id is not None:
                    node = next(
                        (n for n in finding_key.function.nodes if n.node_id == finding_key.node_id),
                        None,
                    )

                if node:
                    res.add(
                        node,
                        {
                            "underlying_type": "interval_analysis",
                            "variable_name": finding_value.variable_name,
                            "has_overflow": finding_value.has_overflow,
                            "has_underflow": finding_value.has_underflow,
                            "var_type": finding_value.var_type,
                        },
                    )

            results.append(res)

        return results
