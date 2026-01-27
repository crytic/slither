"""Data classes for test results in data flow analysis."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class VariableResult:
    """Result for a single variable."""

    name: str
    range_str: str
    overflow: str
    overflow_amount: int = 0


@dataclass
class FunctionResult:
    """Result for a single function analysis."""

    function_name: str
    contract_name: str
    variables: Dict[str, VariableResult] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ContractResult:
    """Result for a single contract analysis."""

    contract_file: str
    contract_name: str
    functions: Dict[str, FunctionResult] = field(default_factory=dict)


@dataclass
class TestComparison:
    """Comparison result between expected and actual."""

    passed: bool
    variable_name: str
    expected_range: Optional[str] = None
    actual_range: Optional[str] = None
    expected_overflow: Optional[str] = None
    actual_overflow: Optional[str] = None
    message: str = ""


@dataclass
class FunctionTestResult:
    """Test result for a single function."""

    function_name: str
    passed: bool
    comparisons: List[TestComparison] = field(default_factory=list)
    missing_expected: List[str] = field(default_factory=list)
    unexpected_vars: List[str] = field(default_factory=list)


@dataclass
class ContractTestResult:
    """Test result for a single contract."""

    contract_file: str
    contract_name: str
    passed: bool
    function_results: Dict[str, FunctionTestResult] = field(default_factory=dict)
    error: Optional[str] = None
