from typing import Dict, Optional

from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval_enhanced.analysis.analysis import IntervalAnalysisEnhanced
from slither.analyses.data_flow.interval_enhanced.analysis.domain import (
    DomainVariant,
    IntervalDomain,
)
from slither.core.cfg.node import Node, NodeType
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type


def analyze_interval(file_path: str):
    try:
        slither = Slither(file_path)
        functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

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

            # Analyze each node's results
            for node, analysis in results.items():

                if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                print(f"\n\tExpression: {node.expression}")
                print("\t" + "-" * 36)

                # Check variable bounds for overflow/underflow
                for var_name, var_info in state.info.items():
                    print(f"\t\t📊 Variable: {var_name}")

                    # Print interval ranges
                    for i, interval_range in enumerate(var_info.interval_ranges):
                        print(f"\t\t\t📈 Range {i+1}: {interval_range}")

                    # Print valid values
                    if not var_info.valid_values.is_empty():
                        print(f"\t\t\t✅ Valid values: {var_info.valid_values}")

                    # Print invalid values
                    if not var_info.invalid_values.is_empty():
                        print(f"\t\t\t❌ Invalid values: {var_info.invalid_values}")

                    # Check for overflow/underflow
                    if var_info.has_overflow():
                        print(f"\t\t\t⚠️  OVERFLOW detected for {var_name}")

                    if var_info.has_underflow():
                        print(f"\t\t\t⚠️  UNDERFLOW detected for {var_name}")

    except Exception as e:
        print(f"Error: {e}")
        return None


if __name__ == "__main__":
    analyze_interval("tests/e2e/detectors/test_data/interval/0.8.10/SimpleSum.sol")
