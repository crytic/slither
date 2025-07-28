#!/usr/bin/env python3
"""
Simplified interval analysis tool for VS Code extension integration
"""

import json
import sys
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Optional

from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval_enhanced.analysis.analysis import (
    IntervalAnalysisEnhanced,
)
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)


@dataclass
class IntervalRangeResult:
    """Serializable representation of an interval range"""

    lower_bound: str
    upper_bound: str

    def __str__(self):
        return f"[{self.lower_bound}, {self.upper_bound}]"


@dataclass
class SingleValuesResult:
    """Serializable representation of single values"""

    values: List[str]

    def __str__(self):
        if not self.values:
            return "{}"
        return "{" + ", ".join(self.values) + "}"


@dataclass
class LocationInfo:
    """Location information for source code elements"""

    line: int
    column: int
    end_line: int
    end_column: int


@dataclass
class VariableResult:
    """Serializable representation of a variable's analysis result"""

    name: str
    canonical_name: str  # Full canonical name for matching
    display_name: str  # Short display name for UI
    interval_ranges: List[IntervalRangeResult]
    valid_values: SingleValuesResult
    invalid_values: SingleValuesResult
    has_overflow: bool
    has_underflow: bool
    var_type: Optional[str] = None
    location: Optional[LocationInfo] = None  # Where variable is defined/used


@dataclass
class NodeResult:
    """Serializable representation of a node's analysis result"""

    expression: str
    node_id: int
    node_type: str
    location: Optional[LocationInfo] = None  # Where the expression is located
    variables: List[VariableResult] = field(default_factory=list)


@dataclass
class FunctionResult:
    """Serializable representation of a function's analysis result"""

    name: str
    nodes: List[NodeResult]


@dataclass
class AnalysisResult:
    """Complete analysis result for a file"""

    file_path: str
    timestamp: str
    functions: List[FunctionResult]


class SimpleIntervalAnalyzer:
    """Simplified interval analyzer for VS Code extension"""

    def format_decimal_value(self, value) -> str:
        """Format decimal value for consistent output"""
        if value == int(value):
            return str(int(value))
        return str(value)

    def convert_interval_range(self, interval_range) -> IntervalRangeResult:
        """Convert IntervalRange to serializable format"""
        return IntervalRangeResult(
            lower_bound=self.format_decimal_value(interval_range.get_lower()),
            upper_bound=self.format_decimal_value(interval_range.get_upper()),
        )

    def convert_single_values(self, single_values) -> SingleValuesResult:
        """Convert SingleValues to serializable format"""
        values = []
        if not single_values.is_empty():
            # Sort values for consistent output
            sorted_values = sorted(single_values.get())
            values = [self.format_decimal_value(val) for val in sorted_values]
        return SingleValuesResult(values=values)

    def extract_location_info(self, node) -> Optional[LocationInfo]:
        """Extract location information from a node"""
        try:
            if hasattr(node, "source_mapping") and node.source_mapping:
                lines = node.source_mapping.lines
                if lines:
                    # Get the first line for start position
                    start_line = lines[0]
                    end_line = lines[-1] if len(lines) > 1 else start_line

                    # For now, we'll use approximate column positions
                    # In a full implementation, you'd parse the source mapping more precisely
                    return LocationInfo(
                        line=start_line,
                        column=0,  # Would need more precise parsing
                        end_line=end_line,
                        end_column=0,  # Would need more precise parsing
                    )
        except Exception:
            pass
        return None

    def extract_variable_info(self, var_name: str, var_info, node) -> VariableResult:
        """Extract comprehensive variable information"""
        # Convert interval ranges
        interval_ranges = [self.convert_interval_range(ir) for ir in var_info.interval_ranges]

        # Convert valid and invalid values
        valid_values = self.convert_single_values(var_info.valid_values)
        invalid_values = self.convert_single_values(var_info.invalid_values)

        # Check for overflow/underflow
        has_overflow = var_info.has_overflow()
        has_underflow = var_info.has_underflow()

        # Extract variable names
        canonical_name = var_name
        display_name = var_name.split(".")[-1] if "." in var_name else var_name

        # Try to find the variable in the function's variables for location info
        location = None
        try:
            # Look for the variable in function variables
            for var in node.function.variables:
                if var.canonical_name == var_name or var.name in var_name:
                    if hasattr(var, "source_mapping") and var.source_mapping:
                        lines = var.source_mapping.lines
                        if lines:
                            location = LocationInfo(
                                line=lines[0],
                                column=0,
                                end_line=lines[-1] if len(lines) > 1 else lines[0],
                                end_column=0,
                            )
                    break
        except Exception:
            pass

        return VariableResult(
            name=var_name,
            canonical_name=canonical_name,
            display_name=display_name,
            interval_ranges=interval_ranges,
            valid_values=valid_values,
            invalid_values=invalid_values,
            has_overflow=has_overflow,
            has_underflow=has_underflow,
            var_type=str(var_info.var_type) if var_info.var_type else None,
            location=location,
        )

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Analyze a Solidity file and return results as JSON-serializable object
        """
        try:
            # Run analysis
            slither = Slither(file_path)
            functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

            # Collect results
            function_results = []

            for function in functions:
                # Run interval analysis
                engine = Engine.new(analysis=IntervalAnalysisEnhanced(), functions=[function])
                engine.run_analysis()
                results = engine.result()

                # Collect node results
                node_results = []

                for node, analysis in results.items():
                    if not hasattr(analysis, "post") or not isinstance(
                        analysis.post, IntervalDomain
                    ):
                        continue

                    if analysis.post.variant != DomainVariant.STATE:
                        continue

                    state = analysis.post.state

                    # Extract node location
                    node_location = self.extract_location_info(node)

                    # Collect variable results
                    variable_results = []

                    for var_name, var_info in state.info.items():
                        var_result = self.extract_variable_info(var_name, var_info, node)
                        variable_results.append(var_result)

                    # Create node result
                    node_result = NodeResult(
                        expression=str(node.expression),
                        node_id=node.node_id,
                        node_type=str(node.type),
                        location=node_location,
                        variables=variable_results,
                    )
                    node_results.append(node_result)

                # Create function result
                function_result = FunctionResult(name=function.name, nodes=node_results)
                function_results.append(function_result)

            # Create complete analysis result
            analysis_result = AnalysisResult(
                file_path=file_path,
                timestamp=datetime.now().isoformat(),
                functions=function_results,
            )

            return analysis_result

        except Exception as e:
            # Return empty result with error info
            return AnalysisResult(
                file_path=file_path,
                timestamp=datetime.now().isoformat(),
                functions=[],
            )


def main():
    """Main function for command line usage"""
    if len(sys.argv) != 2:
        print(json.dumps({"error": "Usage: python interval_analysis_simple.py <file_path>"}))
        sys.exit(1)

    file_path = sys.argv[1]

    try:
        # Suppress logging output
        import logging

        logging.getLogger().setLevel(logging.ERROR)

        # Capture stdout to filter out log messages
        import io

        # Capture stdout to filter out log messages
        stdout_capture = io.StringIO()
        original_stdout = sys.stdout
        sys.stdout = stdout_capture

        analyzer = SimpleIntervalAnalyzer()
        result = analyzer.analyze_file(file_path)

        # Restore stdout
        sys.stdout = original_stdout

        # Output only the JSON result
        print(json.dumps(asdict(result), indent=2))
    except Exception as e:
        # Restore stdout in case of error
        if "original_stdout" in locals():
            sys.stdout = original_stdout

        error_result = {
            "error": str(e),
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "functions": [],
        }
        print(json.dumps(error_result, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
