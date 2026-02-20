"""Pytest configuration and fixtures for rounding analysis tests."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, TypedDict

import pytest

from slither import Slither
from slither.analyses.data_flow.analyses.rounding.analysis.domain import (
    DomainVariant,
)
from slither.analyses.data_flow.analyses.rounding.core.models import (
    AnnotatedFunction,
)
from slither.analyses.data_flow.analyses.rounding.output.cli import (
    RoundingCLI,
)
from slither.analyses.data_flow.engine.analysis import AnalysisState
from slither.core.variables.variable import Variable

CONTRACTS_DIR = Path(__file__).parent / "contracts"

TEST_CONTRACTS: list[str] = [
    "Test_NameInference.sol",
    "Test_Addition.sol",
    "Test_Multiplication.sol",
    "Test_Subtraction.sol",
    "Test_Division.sol",
    "Test_ConditionalRounding.sol",
    "Test_Interprocedural.sol",
    "Test_TupleReturn.sol",
    "Test_LibraryCall.sol",
    "Test_InlineAnnotation.sol",
]


class FunctionResult(TypedDict, total=False):
    """Snapshot-comparable result for a single function."""

    variables: dict[str, str]
    inconsistencies: list[str]
    annotation_mismatches: list[str]


ContractResults = dict[str, dict[str, FunctionResult]]
AnalyzeCallable = Callable[[Path], ContractResults]


@pytest.fixture
def contracts_dir() -> Path:
    """Return the path to test contracts directory."""
    return CONTRACTS_DIR


@pytest.fixture
def analyze_contract() -> AnalyzeCallable:
    """Run the RoundingCLI analysis end-to-end."""
    return _run_analysis


def _run_analysis(contract_path: Path) -> ContractResults:
    """Run the analysis and extract results."""
    slither_instance = Slither(str(contract_path))
    analysis = RoundingCLI()
    analysis.run(slither_instance)

    output: ContractResults = {}
    for annotated in analysis.results:
        _collect_function_result(annotated, output)

    return output


def _collect_function_result(
    annotated: AnnotatedFunction,
    output: ContractResults,
) -> None:
    """Add a single function's results to the output dict."""
    func_result = _extract_results(annotated)
    if not func_result:
        return
    contract_name = annotated.contract_name
    if contract_name not in output:
        output[contract_name] = {}
    output[contract_name][annotated.function_name] = func_result


def _extract_results(
    annotated: AnnotatedFunction,
) -> FunctionResult | None:
    """Extract snapshot-comparable data from AnnotatedFunction."""
    variables: dict[str, str] = {}

    for node, state in annotated.node_results.items():
        if not node.sons:
            _collect_exit_tags(state, variables)

    func_data: FunctionResult = {"variables": variables}

    if annotated.inconsistencies:
        func_data["inconsistencies"] = [
            finding.message for finding in annotated.inconsistencies
        ]
    if annotated.annotation_mismatches:
        func_data["annotation_mismatches"] = [
            finding.message
            for finding in annotated.annotation_mismatches
        ]

    if not variables and not annotated.inconsistencies:
        return None

    return func_data


def _collect_exit_tags(
    state: AnalysisState,
    variables: dict[str, str],
) -> None:
    """Collect variable tags from an exit-node analysis state."""
    if state.post.variant != DomainVariant.STATE:
        return
    post_state = state.post.state
    for variable, tags in post_state._tags.items():
        if not isinstance(variable, Variable):
            continue
        if len(tags) == 1:
            variables[variable.name] = next(iter(tags)).name
        else:
            names = sorted(tag.name for tag in tags)
            variables[variable.name] = "{" + ", ".join(names) + "}"
