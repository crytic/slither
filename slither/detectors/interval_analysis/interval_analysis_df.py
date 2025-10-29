"""
Interval analysis detection
"""

import json
from dataclasses import dataclass
from typing import Dict, List, Optional
from pathlib import Path

from loguru import logger
from slither.analyses.data_flow.analyses.interval.analysis.analysis import IntervalAnalysis
from slither.analyses.data_flow.analyses.interval.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.analyses.data_flow.engine.engine import Engine
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.declarations.function import Function
from slither.core.variables.variable import Variable
from slither.detectors.abstract_detector import AbstractDetector, DetectorClassification
from slither.utils.output import Output

from IPython import embed


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
    node_expression: Optional[str] = None  # Added this


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

    ONLY_SHOW_OVERFLOW = True
    SHOW_TEMP_VARIABLES = True
    SHOW_BOOLEAN_VARIABLES = False
    SHOW_CHECKED_SCOPES = True
    SHOW_WRITTEN_VARIABLES = True
    SHOW_READ_VARIABLES = False
    SHOW_DIVISION_BY_ZERO = False

    def _analyze_function(self, function: Function) -> Dict[FindingKey, List[FindingValue]]:
        """Analyze a single function and return findings."""
        findings: Dict[FindingKey, List[FindingValue]] = {}

        # Run interval analysis
        engine = Engine.new(analysis=IntervalAnalysis(), function=function)
        engine.run_analysis()
        analysis_results = engine.result()

        # Extract findings from each node
        for node, analysis in analysis_results.items():
            # Skip checked scopes - no overflows will happen there
            if node.scope.is_checked and not self.SHOW_CHECKED_SCOPES:
                continue
            if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                continue
            if analysis.post.variant != DomainVariant.STATE:
                continue

            state = analysis.post.state

            # Get variables relevant to this node (exact matches only)
            node_variables = set()
            variables: List[Variable] = []

            if self.SHOW_WRITTEN_VARIABLES:
                variables = variables + node.variables_written
            if self.SHOW_READ_VARIABLES:
                variables = variables + node.variables_read

            if not self.SHOW_WRITTEN_VARIABLES and not self.SHOW_READ_VARIABLES:
                logger.error(
                    "At least one of SHOW_WRITTEN_VARIABLES or SHOW_READ_VARIABLES must be True"
                )
                raise ValueError(
                    "At least one of SHOW_WRITTEN_VARIABLES or SHOW_READ_VARIABLES must be True"
                )

            for var in variables:
                if hasattr(var, "canonical_name"):
                    node_variables.add(var.canonical_name)
                elif hasattr(var, "name"):
                    node_variables.add(var.name)

            if not node_variables:
                continue

            # Check each range variable
            for var_name, range_var in state.get_range_variables().items():

                # Only exact matches
                if var_name not in node_variables:
                    continue

                # Skip booleans, temp variables, and variables ending with dot
                if (
                    range_var.get_var_type() == ElementaryType("bool")
                    and not self.SHOW_BOOLEAN_VARIABLES
                ):
                    continue
                if "TMP" in var_name and not self.SHOW_TEMP_VARIABLES:
                    continue

                if var_name.endswith("."):
                    continue

                # Only include overflow/underflow issues
                has_overflow = range_var.has_overflow()
                has_underflow = range_var.has_underflow()

                if self.ONLY_SHOW_OVERFLOW and not (has_overflow or has_underflow):
                    continue

                interval_ranges = []
                skip_variable = False
                for r in range_var.get_interval_ranges():
                    if "Infinity" in str(r.get_upper()) and not self.SHOW_DIVISION_BY_ZERO:
                        skip_variable = True
                        break
                    if "-Infinity" in str(r.get_lower()) and not self.SHOW_DIVISION_BY_ZERO:
                        skip_variable = True
                        break

                    interval_ranges.append(
                        {
                            "lower": str(r.get_lower()),
                            "upper": str(r.get_upper()),
                        }
                    )

                if skip_variable:
                    continue

                # Create finding
                finding_key = FindingKey(
                    function=function,
                    variable_name=var_name,
                    node_id=node.node_id,
                )

                finding_value = FindingValue(
                    interval_ranges=interval_ranges,
                    valid_values=[str(v) for v in range_var.get_valid_values()],
                    invalid_values=[str(v) for v in range_var.get_invalid_values()],
                    has_overflow=has_overflow,
                    has_underflow=has_underflow,
                    var_type=str(range_var.get_var_type()) if range_var.get_var_type() else None,
                    variable_name=var_name,
                    node_expression=(
                        str(node.expression)
                        if hasattr(node, "expression") and node.expression
                        else None
                    ),
                )

                if finding_key not in findings:
                    findings[finding_key] = []
                findings[finding_key].append(finding_value)

        return findings

    def _analyze_all_contracts(self) -> Dict[FindingKey, List[FindingValue]]:
        """Run analysis on all contracts."""
        all_findings: Dict[FindingKey, List[FindingValue]] = {}

        logger.info("=" * 80)
        logger.info("Starting interval analysis on all contracts")
        logger.info(f"Total contracts: {len(self.contracts)}")
        logger.info("=" * 80)

        for contract in self.contracts:
            logger.info(f"Analyzing contract: {contract.name}")

            for function in contract.functions_and_modifiers_declared:
                if not function.is_implemented or function.is_constructor:
                    continue

                logger.info(f"  Analyzing function: {function.name}")
                function_findings = self._analyze_function(function)
                all_findings.update(function_findings)

                if function_findings:
                    logger.info(f"  ✓ Found {len(function_findings)} findings")

        logger.info("=" * 80)
        logger.info(f"Analysis complete: {len(all_findings)} total findings")
        logger.info("=" * 80)

        return all_findings

    def _findings_to_structured_format(
        self, findings: Dict[FindingKey, List[FindingValue]]
    ) -> List[Dict]:
        """Convert findings dictionary to structured format for JSON output."""
        # Group by contract and function
        grouped = {}

        for finding_key, finding_values in findings.items():
            contract_name = finding_key.function.contract.name
            function_name = finding_key.function.name
            key = (contract_name, function_name)

            if key not in grouped:
                grouped[key] = {
                    "contract": contract_name,
                    "function": function_name,
                    "findings": [],
                }

            for finding_value in finding_values:
                grouped[key]["findings"].append(
                    {
                        "variable_name": finding_key.variable_name,
                        "node_id": finding_key.node_id,
                        "node_expression": finding_value.node_expression,
                        "var_type": finding_value.var_type,
                        "has_overflow": finding_value.has_overflow,
                        "has_underflow": finding_value.has_underflow,
                        "interval_ranges": finding_value.interval_ranges,
                        "valid_values": finding_value.valid_values,
                        "invalid_values": finding_value.invalid_values,
                    }
                )

        return list(grouped.values())

    def _write_json_report(self, structured_results: List[Dict], output_dir: Path):
        """Write JSON report."""
        output_file = output_dir / "interval_analysis_report.json"
        with open(output_file, "w") as f:
            json.dump(structured_results, f, indent=2)
        logger.info(f"JSON report written to: {output_file}")

    def _write_text_report(self, structured_results: List[Dict], output_dir: Path):
        """Write human-readable text report."""
        output_file = output_dir / "interval_analysis_report.txt"

        with open(output_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("INTERVAL ANALYSIS REPORT\n")
            f.write("=" * 80 + "\n\n")

            for contract_function in structured_results:
                f.write(f"Contract: {contract_function['contract']}\n")
                f.write(f"Function: {contract_function['function']}\n")
                f.write("-" * 80 + "\n")

                for finding in contract_function["findings"]:
                    f.write(f"\n  Variable: {finding['variable_name']}\n")
                    if finding["node_id"] is not None:
                        f.write(f"  Node ID: {finding['node_id']}\n")
                    if finding.get("node_expression"):
                        f.write(f"  Expression: {finding['node_expression']}\n")
                    if finding["var_type"]:
                        f.write(f"  Type: {finding['var_type']}\n")

                    # Warnings
                    warnings = []
                    if finding["has_overflow"]:
                        warnings.append("OVERFLOW")
                    if finding["has_underflow"]:
                        warnings.append("UNDERFLOW")
                    if warnings:
                        f.write(f"  ⚠️  WARNINGS: {', '.join(warnings)}\n")

                    # Ranges
                    if finding["interval_ranges"]:
                        range_strs = [
                            f"[{r['lower']}, {r['upper']}]" for r in finding["interval_ranges"]
                        ]
                        f.write(f"  Ranges: {', '.join(range_strs)}\n")

                    # Valid/Invalid values
                    if finding["valid_values"]:
                        f.write(f"  Valid: {', '.join(finding['valid_values'])}\n")
                    if finding["invalid_values"]:
                        f.write(f"  Invalid: {', '.join(finding['invalid_values'])}\n")

                    f.write("\n")

                f.write("=" * 80 + "\n\n")

        logger.info(f"Text report written to: {output_file}")

    def _generate_slither_outputs(
        self, findings: Dict[FindingKey, List[FindingValue]]
    ) -> List[Output]:
        """Generate Slither Output objects for console display."""
        results = []

        # Sort for consistent output
        sorted_findings = sorted(findings.items(), key=lambda x: x[0].function.name)

        for finding_key, finding_values in sorted_findings:
            info = [
                f"Interval analysis for variable '{finding_key.variable_name}' "
                f"in function '{finding_key.function.name}':\n"
            ]

            for finding_value in finding_values:
                # Node info
                if finding_key.node_id is not None:
                    info.append(f"\tNode {finding_key.node_id}")
                    if finding_value.node_expression:
                        info.append(f": {finding_value.node_expression}\n")
                    else:
                        info.append("\n")

                # Type
                if finding_value.var_type:
                    info.append(f"\tType: {finding_value.var_type}\n")

                # Warnings
                warnings = []
                if finding_value.has_overflow:
                    warnings.append("OVERFLOW")
                if finding_value.has_underflow:
                    warnings.append("UNDERFLOW")
                if warnings:
                    info.append(f"\t⚠️  WARNINGS: {', '.join(warnings)}\n")

                # Ranges
                if finding_value.interval_ranges:
                    range_strs = [
                        f"[{r['lower']}, {r['upper']}]" for r in finding_value.interval_ranges
                    ]
                    info.append(f"\tRanges: {', '.join(range_strs)}\n")
                else:
                    info.append("\tRanges: None\n")

                # Values
                info.append(
                    f"\tValid: {', '.join(finding_value.valid_values) if finding_value.valid_values else 'None'}\n"
                )
                info.append(
                    f"\tInvalid: {', '.join(finding_value.invalid_values) if finding_value.invalid_values else 'None'}\n"
                )

            # Create output
            res = self.generate_result(info)
            res.add(finding_key.function)

            # Add node with metadata
            for finding_value in finding_values:
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

    def _detect(self) -> List[Output]:
        """Main detection method."""
        # 1. Run analysis on all contracts
        findings = self._analyze_all_contracts()

        # 2. Convert to structured format
        structured_results = self._findings_to_structured_format(findings)

        # 3. Write reports
        output_dir = Path("interval_analysis_results")
        output_dir.mkdir(exist_ok=True)
        self._write_json_report(structured_results, output_dir)
        self._write_text_report(structured_results, output_dir)

        # 4. Generate Slither outputs for console
        return self._generate_slither_outputs(findings)
