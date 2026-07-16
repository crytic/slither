"""
Golden output snapshot tests for SSA generation.

These tests capture the exact SSA IR output and detect any changes.
If copy_ir() or SSA generation changes, these snapshots will fail,
alerting developers to review the changes.

To update snapshots after intentional changes:
    pytest tests/unit/slithir/test_ssa_snapshot.py --insta update
"""

import re

import pytest

from slither.core.declarations import Function
from slither.slithir.operations import OperationWithLValue, Phi


def normalize_phi_rvalues(text: str) -> str:
    """Sort phi rvalue lists in SSA strings for deterministic output.

    Phi operations like `x := ϕ(['a_2', 'a_1'])` have non-deterministic
    rvalue order. This sorts them to make output stable.
    """

    def sort_phi_list(match: re.Match) -> str:
        # Extract the list content and sort it
        list_content = match.group(1)
        # Parse the list items (they're quoted strings)
        items = re.findall(r"'([^']*)'", list_content)
        sorted_items = sorted(items)
        return "ϕ([" + ", ".join(f"'{item}'" for item in sorted_items) + "])"

    # Match phi operations with their rvalue lists
    pattern = r"ϕ\(\[([^\]]+)\]\)"
    return re.sub(pattern, sort_phi_list, text)


def normalize_ssa_indices(text: str) -> str:
    """Normalize SSA variable indices to make output deterministic.

    Replaces variable indices (e.g., result_1, TMP_5) with sequential numbers
    based on first occurrence, making the output stable across runs.
    """
    # Track seen variables and their normalized indices
    var_mapping: dict[str, str] = {}
    counter = {"local": 0, "tmp": 0, "ref": 0, "state": 0}

    def replace_var(match: re.Match) -> str:
        var_name = match.group(0)
        if var_name not in var_mapping:
            # Determine variable type from prefix/pattern
            if var_name.startswith("TMP_"):
                counter["tmp"] += 1
                var_mapping[var_name] = f"TMP_{counter['tmp']}"
            elif var_name.startswith("REF_"):
                counter["ref"] += 1
                var_mapping[var_name] = f"REF_{counter['ref']}"
            elif "_" in var_name:
                # Local or state variable with index (e.g., result_1, acc_2)
                base = var_name.rsplit("_", 1)[0]
                if base not in var_mapping:
                    var_mapping[base] = base
                counter["local"] += 1
                var_mapping[var_name] = f"{base}_{counter['local']}"
            else:
                var_mapping[var_name] = var_name
        return var_mapping[var_name]

    # Pattern to match SSA variables: name_N or TMP_N or REF_N
    pattern = r"\b(?:TMP_\d+|REF_\d+|[a-z][a-z0-9]*_\d+)\b"
    return re.sub(pattern, replace_var, text)


def format_ssa_output(func: Function, normalize_indices: bool = True) -> str:
    """Format SSA output in a deterministic way for snapshot comparison.

    Args:
        func: Function to format
        normalize_indices: If True, normalize SSA indices for determinism
    """
    lines = []
    lines.append(f"Function: {func.name}")
    lines.append(f"Parameters: {[p.name for p in func.parameters]}")
    lines.append(f"Returns: {[r.name for r in func.returns]}")
    lines.append("")

    for node in func.nodes:
        lines.append(f"Node {node.node_id} ({node.type.name}):")
        if node.expression:
            lines.append(f"  Expression: {node.expression}")

        irs_ssa = list(node.irs_ssa)
        for ir in irs_ssa:
            ir_str = str(ir)
            lines.append(f"  SSA: {ir_str}")

            # Add extra details for operations with lvalue
            if isinstance(ir, OperationWithLValue) and ir.lvalue:
                lvalue = ir.lvalue
                lv_type = type(lvalue).__name__
                lines.append(f"       lvalue: {lvalue} (type={lv_type})")

            # Add phi node details with sorted rvalues for determinism
            if isinstance(ir, Phi):
                # Sort rvalues by string representation for deterministic output
                rvalues = sorted([str(rv) for rv in ir.rvalues])
                lines.append(f"       rvalues: {rvalues}")

        lines.append("")

    output = "\n".join(lines)
    if normalize_indices:
        # First sort phi rvalues (order is non-deterministic in Phi.__str__)
        output = normalize_phi_rvalues(output)
        # Then normalize SSA indices
        output = normalize_ssa_indices(output)
    return output


# =============================================================================
# Test Contracts for Snapshot Testing
# =============================================================================

BASIC_OPERATIONS_CONTRACT = """
pragma solidity ^0.8.15;

contract BasicOps {
    uint256 public stateVar;

    function arithmetic(uint a, uint b) external pure returns (uint) {
        uint sum = a + b;
        uint diff = a - b;
        uint prod = a * b;
        return sum + diff + prod;
    }

    function conditional(uint x) external pure returns (uint) {
        if (x > 10) {
            return x * 2;
        } else {
            return x + 1;
        }
    }

    function loop(uint n) external pure returns (uint) {
        uint sum = 0;
        for (uint i = 0; i < n; i++) {
            sum += i;
        }
        return sum;
    }

    function stateAccess(uint val) external {
        stateVar = val;
        uint local = stateVar + 1;
        stateVar = local;
    }
}
"""


CALLS_CONTRACT = """
pragma solidity ^0.8.15;

interface ITarget {
    function externalFunc(uint) external returns (uint);
}

contract Calls {
    function internalCallTest(uint x) external pure returns (uint) {
        return _helper(x) + _helper(x * 2);
    }

    function _helper(uint val) internal pure returns (uint) {
        return val * 3;
    }

    function externalCallTest(address target, uint x) external returns (uint) {
        return ITarget(target).externalFunc(x);
    }

    function solidityCallTest(bytes memory data) external pure returns (bytes32) {
        return keccak256(data);
    }
}
"""


COMPLEX_TYPES_CONTRACT = """
pragma solidity ^0.8.15;

contract ComplexTypes {
    uint[] public dynamicArray;
    mapping(uint => uint) public myMapping;

    struct Point {
        uint x;
        uint y;
    }

    function arrayOps() external returns (uint) {
        dynamicArray.push(1);
        dynamicArray.push(2);
        uint len = dynamicArray.length;
        uint first = dynamicArray[0];
        delete dynamicArray;
        return len + first;
    }

    function structOps() external pure returns (uint) {
        Point memory p = Point(10, 20);
        return p.x + p.y;
    }

    function tupleOps() external pure returns (uint, uint) {
        (uint a, uint b) = _returnTuple();
        return (a + 1, b + 1);
    }

    function _returnTuple() internal pure returns (uint, uint) {
        return (42, 24);
    }
}
"""


# =============================================================================
# Snapshot Tests
# =============================================================================


def test_basic_operations_ssa(slither_from_solidity_source, snapshot):
    """Snapshot test for basic arithmetic and control flow SSA"""
    with slither_from_solidity_source(BASIC_OPERATIONS_CONTRACT) as slither:
        contracts = slither.get_contract_from_name("BasicOps")
        assert len(contracts) == 1
        contract = contracts[0]

        output_lines = []
        output_lines.append("=" * 60)
        output_lines.append("SSA Snapshot: BasicOps Contract")
        output_lines.append("=" * 60)
        output_lines.append("")

        # Sort functions by name for deterministic output
        functions = sorted(
            [f for f in contract.functions if not f.is_constructor],
            key=lambda f: f.name,
        )

        for func in functions:
            output_lines.append(format_ssa_output(func))
            output_lines.append("-" * 40)
            output_lines.append("")

        actual_output = "\n".join(output_lines)
        assert snapshot() == actual_output


def test_calls_ssa(slither_from_solidity_source, snapshot):
    """Snapshot test for function calls SSA"""
    with slither_from_solidity_source(CALLS_CONTRACT) as slither:
        contracts = slither.get_contract_from_name("Calls")
        assert len(contracts) == 1
        contract = contracts[0]

        output_lines = []
        output_lines.append("=" * 60)
        output_lines.append("SSA Snapshot: Calls Contract")
        output_lines.append("=" * 60)
        output_lines.append("")

        functions = sorted(
            [f for f in contract.functions if not f.is_constructor],
            key=lambda f: f.name,
        )

        for func in functions:
            output_lines.append(format_ssa_output(func))
            output_lines.append("-" * 40)
            output_lines.append("")

        actual_output = "\n".join(output_lines)
        assert snapshot() == actual_output


def test_complex_types_ssa(slither_from_solidity_source, snapshot):
    """Snapshot test for complex types (arrays, structs, tuples) SSA"""
    with slither_from_solidity_source(COMPLEX_TYPES_CONTRACT) as slither:
        contracts = slither.get_contract_from_name("ComplexTypes")
        assert len(contracts) == 1
        contract = contracts[0]

        output_lines = []
        output_lines.append("=" * 60)
        output_lines.append("SSA Snapshot: ComplexTypes Contract")
        output_lines.append("=" * 60)
        output_lines.append("")

        functions = sorted(
            [f for f in contract.functions if not f.is_constructor],
            key=lambda f: f.name,
        )

        for func in functions:
            output_lines.append(format_ssa_output(func))
            output_lines.append("-" * 40)
            output_lines.append("")

        actual_output = "\n".join(output_lines)
        assert snapshot() == actual_output
