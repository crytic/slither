"""Pytest configuration and fixtures for data flow analysis tests."""

import pytest
from pathlib import Path
from typing import Dict, Any

# Path to test contracts - local contracts directory
CONTRACTS_DIR = Path(__file__).parent / "contracts"

# List of contract files with expected results
TEST_CONTRACTS: list[str] = [
    "Test_NameInference.sol",
    "Test_Addition.sol",
    "Test_Multiplication.sol",
    "Test_Subtraction.sol",
    "Test_Division.sol",
    "Test_ConditionalRounding.sol",
    "Test_Interprocedural.sol",
    "Test_TupleReturn.sol",
]


@pytest.fixture
def contracts_dir() -> Path:
    """Return the path to test contracts directory."""
    return CONTRACTS_DIR


@pytest.fixture
def analyze_contract():
    """Fixture providing contract analysis function.

    Returns a function that analyzes a contract file and returns
    results as a dictionary suitable for snapshot comparison.
    """
    from slither import Slither
    from slither.analyses.data_flow.analyses.rounding.analysis.analysis import (
        RoundingAnalysis,
    )
    from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
        DomainVariant,
    )
    from slither.analyses.data_flow.engine.engine import Engine

    def _analyze(contract_path: Path) -> Dict[str, Any]:
        """Analyze a contract and return results as a dictionary."""
        slither = Slither(str(contract_path))
        output: Dict[str, Any] = {}

        for contract in slither.contracts:
            contract_data: Dict[str, Any] = {}

            for function in contract.functions_and_modifiers_declared:
                if not function.is_implemented or function.is_constructor:
                    continue
                if not function.nodes:
                    continue

                analysis = RoundingAnalysis()
                engine = Engine.new(analysis=analysis, function=function)
                engine.run_analysis()
                results = engine.result()

                func_result = _extract_function_results(results, function, analysis)
                if func_result:
                    contract_data[function.name] = func_result

            if contract_data:
                output[contract.name] = contract_data

        return output

    def _extract_function_results(
        results: Dict[Any, Any],
        function: Any,
        analysis: RoundingAnalysis,
    ) -> Dict[str, Any] | None:
        """Extract rounding analysis results from a function."""
        from slither.core.variables.variable import Variable

        # Find exit nodes
        return_nodes = [node for node in function.nodes if not node.sons]
        if not return_nodes and function.nodes:
            return_nodes = [function.nodes[-1]]

        variables: Dict[str, str] = {}

        for node in return_nodes:
            if node not in results:
                continue
            state = results[node]
            if state.post.variant != DomainVariant.STATE:
                continue

            post_state = state.post.state
            for variable, tags in post_state._tags.items():
                if isinstance(variable, Variable):
                    if len(tags) == 1:
                        variables[variable.name] = next(iter(tags)).name
                    else:
                        names = sorted(tag.name for tag in tags)
                        variables[variable.name] = "{" + ", ".join(names) + "}"

        func_data: Dict[str, Any] = {"variables": variables}

        if analysis.inconsistencies:
            func_data["inconsistencies"] = analysis.inconsistencies
        if analysis.annotation_mismatches:
            func_data["annotation_mismatches"] = analysis.annotation_mismatches

        if not variables and not analysis.inconsistencies:
            return None

        return func_data

    return _analyze
