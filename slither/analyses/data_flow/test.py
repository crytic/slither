from decimal import Decimal
from typing import Dict, Optional

from slither import Slither
from slither.analyses.data_flow.engine import Engine
from slither.analyses.data_flow.interval.analysis import IntervalAnalysis
from slither.analyses.data_flow.interval.domain import DomainVariant, IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type
from slither.slithir.operations.return_operation import Return


def analyze_interval(file_path: str):
    try:
        slither = Slither(file_path)
        functions = [f for c in slither.contracts for f in c.functions if f.is_implemented]

        for function in functions:
            print(f"\n🔍 Analyzing function: {function.name}")
            print("=" * 60)

            # Run interval analysis
            engine = Engine.new(analysis=IntervalAnalysis(), functions=[function])
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
                    print(f"\t\t📊 Variable: {var_name}, bounds: {var_info}")

                    # Check for type bound violations using IntervalInfo's built-in methods
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

                # Check for return type violations
                check_return_type_violations(node, state, function)

                print("\t" + "-" * 56)

    except Exception as e:
        print(f"Error: {e}")
        return None


def check_return_type_violations(node: Node, state, function):
    """Check if return values exceed function return type bounds"""
    if not hasattr(node, "irs") or not node.irs:
        return

    for ir in node.irs:
        if isinstance(ir, Return):
            function_return_type = function.return_type
            if not function_return_type or len(function_return_type) != 1:
                continue

            return_type = function_return_type[0]
            if not isinstance(return_type, ElementaryType):
                continue

            return_values = ir.values
            if not return_values or len(return_values) != 1:
                continue

            returned_var = return_values[0]

            # Get variable name for lookup
            if hasattr(returned_var, "name"):
                var_name = returned_var.name
            elif hasattr(returned_var, "canonical_name"):
                var_name = returned_var.canonical_name
            else:
                continue

            if var_name in state.info:
                returned_interval = state.info[var_name]
                target_min, target_max = get_type_bounds_for_elementary_type(return_type)

                if returned_interval.upper_bound > target_max:
                    print_return_violation(
                        "overflow", function.name, return_type, returned_interval, target_max, node
                    )

                if returned_interval.lower_bound < target_min:
                    print_return_violation(
                        "underflow", function.name, return_type, returned_interval, target_min, node
                    )


def get_type_bounds_for_elementary_type(elem_type: ElementaryType) -> tuple[Decimal, Decimal]:
    """Get min/max bounds for an elementary type"""
    type_name = elem_type.name

    if type_name.startswith("uint"):
        if type_name == "uint" or type_name == "uint256":
            return Decimal("0"), Decimal(
                "115792089237316195423570985008687907853269984665640564039457584007913129639935"
            )
        else:
            try:
                bits = int(type_name[4:])
                max_val = (2**bits) - 1
                return Decimal("0"), Decimal(str(max_val))
            except ValueError:
                return Decimal("0"), Decimal(
                    "115792089237316195423570985008687907853269984665640564039457584007913129639935"
                )

    elif type_name.startswith("int"):
        if type_name == "int" or type_name == "int256":
            return Decimal(
                "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
            ), Decimal(
                "57896044618658097711785492504343953926634992332820282019728792003956564819967"
            )
        else:
            try:
                bits = int(type_name[3:])
                max_val = (2 ** (bits - 1)) - 1
                min_val = -(2 ** (bits - 1))
                return Decimal(str(min_val)), Decimal(str(max_val))
            except ValueError:
                return Decimal(
                    "-57896044618658097711785492504343953926634992332820282019728792003956564819968"
                ), Decimal(
                    "57896044618658097711785492504343953926634992332820282019728792003956564819967"
                )

    return Decimal("0"), Decimal(
        "115792089237316195423570985008687907853269984665640564039457584007913129639935"
    )


def print_bounds_violation(
    violation_type: str,
    var_name: str,
    var_info: IntervalInfo,
    var_type_range: IntervalInfo,
    node: Node,
):
    """Print variable bounds violation"""
    print(f"🚨 [VIOLATION] {violation_type.upper()} DETECTED")
    print(f"        Variable: {var_name}")
    print(f"        Type bounds: {var_type_range}")
    print(f"        Actual bounds: {var_info}")


def print_return_violation(
    violation_type: str,
    function_name: str,
    return_type: ElementaryType,
    actual_interval: IntervalInfo,
    type_bound: Decimal,
    node: Node,
):
    """Print return type violation"""
    print(f"🚨 [VIOLATION] RETURN {violation_type.upper()} DETECTED")
    print(f"        Function: {function_name}")
    print(f"        Return type: {return_type.name}")
    print(f"        Type bound: {type_bound}")
    print(f"        Actual bounds: {actual_interval}")


if __name__ == "__main__":
    analyze_interval("tests/e2e/detectors/test_data/interval/0.8.10/FunctionCalls.sol")
