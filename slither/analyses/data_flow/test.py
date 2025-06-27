from typing import Dict, Optional
from loguru import logger
from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval import (
    DomainVariant,
    IntervalAnalysis,
    IntervalDomain,
    IntervalInfo,
)
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type


def analyze_interval(file_path: str):
    try:

        slither = Slither(file_path)
        functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

        for function in functions:

            # Run reentrancy analysis
            engine = Engine.new(analysis=IntervalAnalysis(), functions=[function])
            engine.run_analysis()
            results = engine.result()

            var_mapping: Dict[str, Type] = {}
            for var in function.variables:
                key: Optional[str] = (
                    var.canonical_name if var.canonical_name is not None else var.name
                )
                if key is not None and isinstance(var.type, ElementaryType):
                    var_mapping[key] = var.type

            for node, analysis in results.items():

                if not hasattr(analysis, "post") or not isinstance(analysis.post, IntervalDomain):
                    continue

                if analysis.post.variant != DomainVariant.STATE:
                    continue

                state = analysis.post.state

                for var_name, var_info in state.info.items():
                    print(f"🔍 Variable: {var_name}, info: {var_info}")

                    if var_info.has_overflow():
                        type_min, type_max = var_info.get_type_bounds()
                        type_bounds = IntervalInfo(
                            upper_bound=type_max, lower_bound=type_min, var_type=var_info.var_type
                        )
                        print_bounds_violation("overflow", var_name, var_info, type_bounds, node)

                    if var_info.has_underflow():
                        type_min, type_max = var_info.get_type_bounds()
                        type_bounds = IntervalInfo(
                            upper_bound=type_max, lower_bound=type_min, var_type=var_info.var_type
                        )
                        print_bounds_violation("underflow", var_name, var_info, type_bounds, node)

    except Exception as e:
        print(f"Error: {e}")
        return None


def print_bounds_violation(
    violation_type: str,
    var_name: str,
    var_info: IntervalInfo,
    var_type_range: IntervalInfo,
    node: Node,
):
    print(f"🚨 {violation_type.upper()} DETECTED 🚨")
    print(f"  Expression: {node.expression}")
    print(f"  Variable: {var_name}")
    print(f"  Bounds: {var_type_range}")
    print(f"  Actual value: {var_info}")

    print("-" * 50)


if __name__ == "__main__":
    analyze_interval("tests/e2e/detectors/test_data/interval/0.8.10/IntervalAnalysisTest.sol")
