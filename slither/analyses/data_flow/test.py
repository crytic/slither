from typing import Dict, Optional
from loguru import logger
from slither import Slither
from slither.analyses.data_flow.engine import Engine

from slither.analyses.data_flow.interval.analysis import IntervalAnalysis
from slither.analyses.data_flow.interval.domain import DomainVariant, IntervalDomain
from slither.analyses.data_flow.interval.info import IntervalInfo
from slither.core.cfg.node import Node
from slither.core.solidity_types.elementary_type import ElementaryType
from slither.core.solidity_types.type import Type


def print_separator(char="=", length=80):
    """Print a separator line"""
    print(char * length)


def print_function_header(function_name, contract_name):
    """Print formatted function header"""
    print_separator("=")
    print(f"ANALYZING FUNCTION: {contract_name}.{function_name}")
    print_separator("=")


def print_node_header(node_index, node):
    """Print formatted node information"""
    if node.expression:
        print(f"{node.expression}")


def print_variable_state(state, title="Variable State"):
    """Print formatted variable state information"""
    if not state.info:
        return

    # Sort variables for consistent output
    sorted_vars = sorted(state.info.items())

    for var_name, var_info in sorted_vars:
        overflow_status = " 🚨 [OVERFLOW]" if var_info.has_overflow() else ""
        underflow_status = " 🚨 [UNDERFLOW]" if var_info.has_underflow() else ""
        status = f"{overflow_status}{underflow_status}"

        print(f"   {var_name}: {var_info}{status}")
    print()


def print_overflow_summary(var_name, var_info, node):
    """Print detailed overflow information"""
    print_separator("!", 50)
    print(f"🚨 OVERFLOW DETECTED")
    print(f"   Function: {node.function.name}")
    print(f"   Variable: {var_name}")
    print(f"   Current bounds: {var_info}")

    if var_info.var_type:
        type_min, type_max = var_info.get_type_bounds()
        print(f"   Type bounds: [{type_min}, {type_max}]")
        print(f"   Type: {var_info.var_type}")

    print(f"   Node: {node.type}")
    print(f"   Expression: {node.expression}")
    print_separator("!", 50)


def print_underflow_summary(var_name, var_info, node):
    """Print detailed underflow information"""
    print_separator("!", 50)
    print(f"🚨 UNDERFLOW DETECTED")
    print(f"   Function: {node.function.name}")
    print(f"   Variable: {var_name}")
    print(f"   Current bounds: {var_info}")

    if var_info.var_type:
        type_min, type_max = var_info.get_type_bounds()
        print(f"   Type bounds: [{type_min}, {type_max}]")
        print(f"   Type: {var_info.var_type}")

    print(f"   Node: {node.type}")
    print(f"   Expression: {node.expression}")
    print_separator("!", 50)


def analyze_interval(file_path: str):
    """Main analysis function with enhanced output formatting"""
    try:
        print_separator("=", 80)
        print("STARTING INTERVAL ANALYSIS")
        print_separator("=", 80)

        slither = Slither(file_path)
        contracts = [c for c in slither.contracts if not c.is_interface and not c.is_library]

        print(f"\nFound {len(contracts)} contract(s) to analyze")
        for contract in contracts:
            print(f"   - {contract.name}")

        total_vulnerabilities = 0

        for contract in contracts:
            functions = [f for f in contract.functions if f.is_implemented and not f.is_constructor]

            print(f"\nCONTRACT: {contract.name}")
            print(f"   Functions to analyze: {len(functions)}")

            for function in functions:
                print_function_header(function.name, contract.name)

                # Print function parameters
                if function.parameters:
                    print("Function Parameters:")
                    for param in function.parameters:
                        print(f"   {param.name}: {param.type}")
                else:
                    print("No parameters")

                # Run interval analysis
                engine = Engine.new(analysis=IntervalAnalysis(), functions=[function])
                engine.run_analysis()
                results = engine.result()

                # Create variable type mapping
                var_mapping: Dict[str, Type] = {}
                for var in function.variables:
                    key: Optional[str] = (
                        var.canonical_name if var.canonical_name is not None else var.name
                    )
                    if key is not None and isinstance(var.type, ElementaryType):
                        var_mapping[key] = var.type

                # Process results for each node
                function_vulnerabilities = 0
                analyzed_nodes = 0

                # Sort nodes by their order in the function
                sorted_results = sorted(
                    results.items(), key=lambda x: x[0].node_id if hasattr(x[0], "node_id") else 0
                )

                for node, analysis in sorted_results:
                    analyzed_nodes += 1

                    if not hasattr(analysis, "post") or not isinstance(
                        analysis.post, IntervalDomain
                    ):
                        continue

                    if analysis.post.variant != DomainVariant.STATE:
                        continue

                    state = analysis.post.state

                    # Only print nodes that have interesting state changes
                    if state.info:
                        print_node_header(analyzed_nodes, node)
                        print_variable_state(state)

                        # Check for vulnerabilities
                        for var_name, var_info in state.info.items():
                            if var_info.has_overflow():
                                print_overflow_summary(var_name, var_info, node)
                                function_vulnerabilities += 1

                            if var_info.has_underflow():
                                print_underflow_summary(var_name, var_info, node)
                                function_vulnerabilities += 1

                # Function summary
                print_separator("=")
                print(f"FUNCTION SUMMARY: {function.name}")
                print(f"   Nodes analyzed: {analyzed_nodes}")
                print(f"   Vulnerabilities found: {function_vulnerabilities}")
                print_separator("=")

                total_vulnerabilities += function_vulnerabilities

        # Final summary
        print_separator("=", 80)
        print("ANALYSIS COMPLETE")
        print(f"   Total vulnerabilities found: {total_vulnerabilities}")
        print_separator("=", 80)

        return total_vulnerabilities

    except Exception as e:
        print_separator("=", 80)
        print(f"ERROR: {e}")
        print_separator("=", 80)
        import traceback

        traceback.print_exc()
        return None


if __name__ == "__main__":
    # Test with the original test file
    vulnerabilities = analyze_interval(
        "tests/e2e/detectors/test_data/interval/0.8.10/EqualityInequalityTest.sol"
    )

    if vulnerabilities is not None:
        print(f"\nAnalysis completed successfully!")
        print(f"Found {vulnerabilities} potential vulnerabilities")
    else:
        print(f"\nAnalysis failed!")
