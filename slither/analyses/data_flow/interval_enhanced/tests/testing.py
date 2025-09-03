import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime

from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval_enhanced.analysis.analysis import IntervalAnalysisEnhanced
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type


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
class VariableResult:
    """Serializable representation of a variable's analysis result"""

    name: str
    interval_ranges: List[IntervalRangeResult]
    valid_values: SingleValuesResult
    invalid_values: SingleValuesResult
    has_overflow: bool
    has_underflow: bool
    var_type: Optional[str]


@dataclass
class NodeResult:
    """Serializable representation of a node's analysis result"""

    expression: str
    variables: List[VariableResult]


@dataclass
class FunctionResult:
    """Serializable representation of a function's analysis result"""

    name: str
    nodes: List[NodeResult]


@dataclass
class TestResult:
    """Complete test result for a file"""

    file_path: str
    timestamp: str
    functions: List[FunctionResult]


class TestOutputManager:
    """Manages test output saving and comparison"""

    def __init__(self, output_dir: str = None):
        # Get the directory where this script is located
        script_dir = Path(__file__).parent
        # Set default output directory relative to script location
        if output_dir is None:
            self.output_dir = script_dir.parent / "output"
        else:
            self.output_dir = Path(output_dir)

        self.output_dir.mkdir(exist_ok=True)
        print(f"📁 Using output directory: {self.output_dir.absolute()}")

    def get_output_file_path(self, input_file_path: str) -> Path:
        """Generate output file path based on input file path"""
        input_path = Path(input_file_path)
        output_filename = f"{input_path.stem}_output.json"
        return self.output_dir / output_filename

    def wipe_output_file(self, output_file: Path) -> None:
        """Remove existing output file if it exists"""
        if output_file.exists():
            print(f"⚠️  About to delete existing output file: {output_file}")
            print("Type 'WIPE' to confirm deletion:")

            try:
                confirmation = input().strip()
                if confirmation == "WIPE":
                    output_file.unlink()
                    print(f"🗑️  Wiped existing output file: {output_file}")
                else:
                    print(f"❌ Deletion cancelled. Expected 'WIPE', got '{confirmation}'")
                    raise ValueError("User cancelled wipe operation")
            except KeyboardInterrupt:
                print("\n❌ Deletion cancelled by user")
                raise ValueError("User cancelled wipe operation")
        else:
            print(f"ℹ️  No existing output file to wipe: {output_file}")

    def save_test_result(self, test_result: TestResult, output_file: Path) -> None:
        """Save test result to JSON file"""
        with open(output_file, "w") as f:
            json.dump(asdict(test_result), f, indent=2)
        print(f"✅ Test output saved to: {output_file}")

    def load_expected_result(self, output_file: Path) -> Optional[TestResult]:
        """Load expected test result from JSON file"""
        try:
            with open(output_file, "r") as f:
                data = json.load(f)
                return TestResult(
                    **{
                        "file_path": data["file_path"],
                        "timestamp": data["timestamp"],
                        "functions": [
                            FunctionResult(
                                **{
                                    "name": func["name"],
                                    "nodes": [
                                        NodeResult(
                                            **{
                                                "expression": node["expression"],
                                                "variables": [
                                                    VariableResult(
                                                        **{
                                                            "name": var["name"],
                                                            "interval_ranges": [
                                                                IntervalRangeResult(**range_data)
                                                                for range_data in var[
                                                                    "interval_ranges"
                                                                ]
                                                            ],
                                                            "valid_values": SingleValuesResult(
                                                                **var["valid_values"]
                                                            ),
                                                            "invalid_values": SingleValuesResult(
                                                                **var["invalid_values"]
                                                            ),
                                                            "has_overflow": var["has_overflow"],
                                                            "has_underflow": var["has_underflow"],
                                                            "var_type": var["var_type"],
                                                        }
                                                    )
                                                    for var in node["variables"]
                                                ],
                                            }
                                        )
                                        for node in func["nodes"]
                                    ],
                                }
                            )
                            for func in data["functions"]
                        ],
                    }
                )
        except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
            print(f"❌ Error loading expected result: {e}")
            return None

    def compare_results(self, actual: TestResult, expected: TestResult) -> bool:
        """Compare actual vs expected results"""
        differences = []

        # Compare function count
        if len(actual.functions) != len(expected.functions):
            differences.append(
                f"Function count mismatch: actual={len(actual.functions)}, expected={len(expected.functions)}"
            )

        # Compare each function
        actual_funcs = {f.name: f for f in actual.functions}
        expected_funcs = {f.name: f for f in expected.functions}

        for func_name in expected_funcs:
            if func_name not in actual_funcs:
                differences.append(f"Missing function: {func_name}")
                continue

            actual_func = actual_funcs[func_name]
            expected_func = expected_funcs[func_name]

            # Compare nodes
            if len(actual_func.nodes) != len(expected_func.nodes):
                differences.append(
                    f"Node count mismatch in {func_name}: actual={len(actual_func.nodes)}, expected={len(expected_func.nodes)}"
                )

            for i, (actual_node, expected_node) in enumerate(
                zip(actual_func.nodes, expected_func.nodes)
            ):
                if actual_node.expression != expected_node.expression:
                    differences.append(
                        f"Expression mismatch in {func_name} node {i}: actual='{actual_node.expression}', expected='{expected_node.expression}'"
                    )

                # Compare variables
                actual_vars = {v.name: v for v in actual_node.variables}
                expected_vars = {v.name: v for v in expected_node.variables}

                for var_name in expected_vars:
                    if var_name not in actual_vars:
                        differences.append(f"Missing variable {var_name} in {func_name} node {i}")
                        continue

                    actual_var = actual_vars[var_name]
                    expected_var = expected_vars[var_name]

                    # Compare variable properties
                    if actual_var.has_overflow != expected_var.has_overflow:
                        differences.append(
                            f"Overflow status mismatch for {var_name} in {func_name}: actual={actual_var.has_overflow}, expected={expected_var.has_overflow}"
                        )

                    if actual_var.has_underflow != expected_var.has_underflow:
                        differences.append(
                            f"Underflow status mismatch for {var_name} in {func_name}: actual={actual_var.has_underflow}, expected={expected_var.has_underflow}"
                        )

                    # Compare interval ranges
                    if len(actual_var.interval_ranges) != len(expected_var.interval_ranges):
                        differences.append(
                            f"Interval range count mismatch for {var_name} in {func_name}: actual={len(actual_var.interval_ranges)}, expected={len(expected_var.interval_ranges)}"
                        )

                    for j, (actual_range, expected_range) in enumerate(
                        zip(actual_var.interval_ranges, expected_var.interval_ranges)
                    ):
                        if (
                            actual_range.lower_bound != expected_range.lower_bound
                            or actual_range.upper_bound != expected_range.upper_bound
                        ):
                            differences.append(
                                f"Range {j} mismatch for {var_name} in {func_name}: actual={actual_range}, expected={expected_range}"
                            )

                    # Compare valid values
                    if set(actual_var.valid_values.values) != set(expected_var.valid_values.values):
                        differences.append(
                            f"Valid values mismatch for {var_name} in {func_name}: actual={actual_var.valid_values}, expected={expected_var.valid_values}"
                        )

                    # Compare invalid values
                    if set(actual_var.invalid_values.values) != set(
                        expected_var.invalid_values.values
                    ):
                        differences.append(
                            f"Invalid values mismatch for {var_name} in {func_name}: actual={actual_var.invalid_values}, expected={expected_var.invalid_values}"
                        )

        # Print results
        if differences:
            print("❌ TEST FAILED - Differences found:")
            for diff in differences:
                print(f"  • {diff}")
            return False
        else:
            print("✅ TEST PASSED - All results match expected output")
            return True


class IntervalAnalyzer:
    """Enhanced interval analyzer with output management"""

    def __init__(self, output_dir: str = None):
        self.output_manager = TestOutputManager(output_dir)

    def format_decimal_value(self, value) -> str:
        """Format decimal value for consistent output"""
        try:
            if value == int(value):
                return str(int(value))
            return str(value)
        except (ValueError, OverflowError):
            # Handle infinity values
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

    def analyze_interval(
        self,
        file_path: str,
        save_output: bool = True,
        compare_output: bool = True,
        wipe_output: bool = False,
    ) -> bool:
        """
        Analyze intervals and optionally save/compare output

        Args:
            file_path: Path to the Solidity file to analyze
            save_output: Whether to save output on first run
            compare_output: Whether to compare with expected output
            wipe_output: Whether to wipe existing output file before analysis

        Returns:
            True if analysis passes (or first run), False if comparison fails
        """
        try:
            # Get output file path
            output_file = self.output_manager.get_output_file_path(file_path)

            # Handle wipe flag
            if wipe_output:
                try:
                    self.output_manager.wipe_output_file(output_file)
                except ValueError as e:
                    if "User cancelled wipe operation" in str(e):
                        print("🛑 Analysis cancelled due to wipe operation being cancelled")
                        return False
                    else:
                        raise e

            # Check if this is first run or comparison run
            is_first_run = not output_file.exists()

            if is_first_run:
                print(f"🔄 First run detected - will save output to {output_file}")
            else:
                print(f"🔄 Comparing with expected output from {output_file}")

            # Run analysis
            slither = Slither(file_path)
            # functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

            # for contract in slither.contracts:
            #     if "Settlement" == contract.name:
            #         settlement_contract = contract

            # functions = (
            #     [
            #         f
            #         for f in settlement_contract.functions
            #         if f.name == "_settleOrder" and f.is_implemented
            #     ]
            #     if settlement_contract
            #     else []
            # )

            functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]
            # Collect results
            function_results = []

            for function in functions:
                print(f"\n🔍 Analyzing function: {function.name}")
                print("=" * 60)

                # Run interval analysis
                engine = Engine.new(analysis=IntervalAnalysisEnhanced(), functions=[function])
                engine.run_analysis()
                results = engine.result()

                # Build variable type mapping for overflow detection
                var_mapping: Dict[str, Type] = {}
                for var in function.variables:
                    key: Optional[str] = (
                        var.canonical_name if var.canonical_name is not None else var.name
                    )
                    if key is not None and isinstance(var.type, ElementaryType):
                        var_mapping[key] = var.type

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

                    print(f"\n\tExpression: {node.expression} --- {node.type} --- {node.node_id}")
                    print("\t" + "-" * 36)

                    # Collect variable results
                    variable_results = []

                    for var_name, var_info in state.info.items():
                        if "TMP" in var_name:
                            continue
                        print(f"\t\t📊 Variable: {var_name}")

                        # Optimize the state info
                        optimized_var_info = var_info.optimize()

                        # Convert interval ranges
                        interval_ranges = [
                            self.convert_interval_range(ir)
                            for ir in optimized_var_info.interval_ranges
                        ]

                        # Print interval ranges
                        for i, interval_range in enumerate(interval_ranges):
                            print(f"\t\t\t📈 Range {i+1}: {interval_range}")

                        # Convert and print valid values
                        valid_values = self.convert_single_values(optimized_var_info.valid_values)
                        if valid_values.values:
                            print(f"\t\t\t✅ Valid values: {valid_values}")

                        # Convert and print invalid values
                        invalid_values = self.convert_single_values(
                            optimized_var_info.invalid_values
                        )
                        if invalid_values.values:
                            print(f"\t\t\t❌ Invalid values: {invalid_values}")

                        # Check for overflow/underflow
                        has_overflow = optimized_var_info.has_overflow()
                        has_underflow = optimized_var_info.has_underflow()

                        if has_overflow:
                            print(f"\t\t\t⚠️  OVERFLOW detected for {var_name}")

                        if has_underflow:
                            print(f"\t\t\t⚠️  UNDERFLOW detected for {var_name}")

                        # Create variable result
                        var_result = VariableResult(
                            name=var_name,
                            interval_ranges=interval_ranges,
                            valid_values=valid_values,
                            invalid_values=invalid_values,
                            has_overflow=has_overflow,
                            has_underflow=has_underflow,
                            var_type=(
                                str(optimized_var_info.var_type)
                                if optimized_var_info.var_type
                                else None
                            ),
                        )
                        variable_results.append(var_result)

                    # Create node result
                    node_result = NodeResult(
                        expression=str(node.expression), variables=variable_results
                    )
                    node_results.append(node_result)

                # Create function result
                function_result = FunctionResult(name=function.name, nodes=node_results)
                function_results.append(function_result)

            # Create complete test result
            test_result = TestResult(
                file_path=file_path,
                timestamp=datetime.now().isoformat(),
                functions=function_results,
            )

            # Handle first run vs comparison
            if is_first_run:
                if save_output:
                    self.output_manager.save_test_result(test_result, output_file)
                print(f"\n✅ Analysis complete - output saved for future comparison")
                return True
            else:
                if compare_output:
                    expected_result = self.output_manager.load_expected_result(output_file)
                    if expected_result:
                        return self.output_manager.compare_results(test_result, expected_result)
                    else:
                        print("❌ Failed to load expected results")
                        return False
                else:
                    print(f"\n✅ Analysis complete - comparison skipped")
                    return True

        except Exception as e:
            print(f"❌ Error during analysis: {e}")
            return False

    def analyze_interval_json(
        self,
        file_path: str,
    ) -> TestResult:
        """
        Analyze intervals and return results as JSON-serializable object

        Args:
            file_path: Path to the Solidity file to analyze

        Returns:
            TestResult object with analysis results
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

                # Build variable type mapping for overflow detection
                var_mapping: Dict[str, Type] = {}
                for var in function.variables:
                    key: Optional[str] = (
                        var.canonical_name if var.canonical_name is not None else var.name
                    )
                    if key is not None and isinstance(var.type, ElementaryType):
                        var_mapping[key] = var.type

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

                    # Collect variable results
                    variable_results = []

                    for var_name, var_info in state.info.items():
                        # Convert interval ranges
                        interval_ranges = [
                            self.convert_interval_range(ir) for ir in var_info.interval_ranges
                        ]

                        # Convert valid and invalid values
                        valid_values = self.convert_single_values(var_info.valid_values)
                        invalid_values = self.convert_single_values(var_info.invalid_values)

                        # Check for overflow/underflow
                        has_overflow = var_info.has_overflow()
                        has_underflow = var_info.has_underflow()

                        # Create variable result
                        var_result = VariableResult(
                            name=var_name,
                            interval_ranges=interval_ranges,
                            valid_values=valid_values,
                            invalid_values=invalid_values,
                            has_overflow=has_overflow,
                            has_underflow=has_underflow,
                            var_type=str(var_info.var_type) if var_info.var_type else None,
                        )
                        variable_results.append(var_result)

                    # Create node result
                    node_result = NodeResult(
                        expression=str(node.expression), variables=variable_results
                    )
                    node_results.append(node_result)

                # Create function result
                function_result = FunctionResult(name=function.name, nodes=node_results)
                function_results.append(function_result)

            # Create complete test result
            test_result = TestResult(
                file_path=file_path,
                timestamp=datetime.now().isoformat(),
                functions=function_results,
            )

            return test_result

        except Exception as e:
            # Return empty result with error info
            return TestResult(
                file_path=file_path,
                timestamp=datetime.now().isoformat(),
                functions=[],
            )


def main():
    """Main function with argparse support"""
    parser = argparse.ArgumentParser(
        description="Interval analysis testing tool for Solidity smart contracts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python testing.py contract.sol                    # Run analysis with save/compare
  python testing.py contract.sol --no-save          # Skip saving output
  python testing.py contract.sol --no-compare       # Skip comparison
  python testing.py contract.sol --wipe             # Reset baseline and create new
  python testing.py contract.sol --output-dir /tmp  # Use custom output directory
  python testing.py contract.sol --json             # Output JSON for VS Code extension
        """,
    )

    parser.add_argument("solidity_file", help="Path to the Solidity file to analyze")

    parser.add_argument(
        "--no-save",
        action="store_true",
        help="Don't save output on first run (default: save output)",
    )

    parser.add_argument(
        "--no-compare",
        action="store_true",
        help="Don't compare with expected output (default: compare if baseline exists)",
    )

    parser.add_argument(
        "--wipe",
        action="store_true",
        help="Reset the baseline by wiping existing output file before analysis",
    )

    parser.add_argument(
        "--output-dir", help="Custom output directory (default: ../output relative to this script)"
    )

    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON for VS Code extension",
    )

    args = parser.parse_args()

    # Validate file exists
    if not Path(args.solidity_file).exists():
        print(f"❌ Error: File '{args.solidity_file}' does not exist")
        return 1

    # Create analyzer with custom output directory if specified
    analyzer = IntervalAnalyzer(output_dir=args.output_dir)

    # Handle JSON output mode
    if args.json:
        try:
            result = analyzer.analyze_interval_json(file_path=args.solidity_file)
            print(json.dumps(asdict(result), indent=2))
            return 0
        except Exception as e:
            error_result = {
                "error": str(e),
                "file_path": args.solidity_file,
                "timestamp": datetime.now().isoformat(),
                "functions": [],
            }
            print(json.dumps(error_result, indent=2))
            return 1

    # Run analysis in normal mode
    success = analyzer.analyze_interval(
        file_path=args.solidity_file,
        save_output=not args.no_save,
        compare_output=not args.no_compare,
        wipe_output=args.wipe,
    )

    if success:
        print("\n🎉 Test completed successfully!")
        return 0
    else:
        print("\n💥 Test failed!")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
