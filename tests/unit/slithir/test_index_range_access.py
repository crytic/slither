"""
Array slices (IndexRangeAccess, `data[start:end]`) are lowered to an IndexRange operation
that reads the base and both bounds (issue #2291)
"""

from slither.analyses.data_dependency.data_dependency import is_dependent
from slither.core.declarations import Function, SolidityVariableComposed
from slither.slithir.operations import Assignment, IndexRange, InitArray
from slither.slithir.variables import Constant

SOURCE = """
pragma solidity ^0.8.19;
contract C {
    uint256 start = 4;
    uint256 end = 36;
    uint256 other = 8;

    function both(bytes calldata data) external view returns (bytes calldata) {
        return data[start:end];
    }

    function noStart(bytes calldata data) external view returns (bytes calldata) {
        return data[:end];
    }

    function noEnd(bytes calldata data) external view returns (bytes calldata) {
        return data[start:];
    }

    function noBounds(bytes calldata data) external pure returns (bytes calldata) {
        return data[:];
    }

    function msgData() external view returns (bytes4, bytes calldata) {
        return (bytes4(msg.data[:4]), msg.data[start:]);
    }

    function nested(bytes calldata data) external view returns (bytes calldata) {
        return data[start:][:end];
    }

    function ternary(bytes calldata data, bool c) external view returns (bytes calldata) {
        return data[c ? start : other:];
    }

    function arraySlice(uint256[] calldata arr) external view returns (uint256) {
        uint256[] calldata r = arr[start:end];
        return r[0];
    }
}
"""


def _index_ranges(f: Function, ssa: bool = False) -> list[IndexRange]:
    return [
        ir
        for node in f.nodes
        for ir in (node.irs_ssa if ssa else node.irs)
        if isinstance(ir, IndexRange)
    ]


def test_index_range_access(slither_from_solidity_source):
    with slither_from_solidity_source(SOURCE) as slither:
        c = slither.get_contract_from_name("C")[0]
        start = c.get_state_variable_from_name("start")
        end = c.get_state_variable_from_name("end")
        other = c.get_state_variable_from_name("other")

        # data[start:end]
        f = c.get_function_from_signature("both(bytes)")
        (ir,) = _index_ranges(f)
        data = f.parameters[0]
        assert ir.base == data
        assert ir.start == start
        assert ir.end == end
        assert ir.read == [data, start, end]
        assert str(ir.lvalue.type) == "bytes"
        assert str(f.nodes[1].expression) == "data[start:end]"
        assert set(f.state_variables_read) == {start, end}
        assert is_dependent(ir.lvalue, start, f)
        assert is_dependent(ir.lvalue, end, f)
        assert is_dependent(ir.lvalue, data, f)

        # SSA copy keeps the bounds
        (ir_ssa,) = _index_ranges(f, ssa=True)
        assert ir_ssa.start.non_ssa_version == start
        assert ir_ssa.end.non_ssa_version == end

        # Omitted bounds
        (ir,) = _index_ranges(c.get_function_from_signature("noStart(bytes)"))
        assert ir.start is None and ir.end == end
        (ir,) = _index_ranges(c.get_function_from_signature("noEnd(bytes)"))
        assert ir.start == start and ir.end is None
        f = c.get_function_from_signature("noBounds(bytes)")
        (ir,) = _index_ranges(f)
        assert ir.start is None and ir.end is None
        assert ir.read == [f.parameters[0]]
        assert len(_index_ranges(f, ssa=True)) == 1

        # msg.data slices
        f = c.get_function_from_signature("msgData()")
        first, second = _index_ranges(f)
        assert first.base == SolidityVariableComposed("msg.data")
        assert isinstance(first.end, Constant) and first.end.value == 4
        assert second.start == start
        assert set(f.state_variables_read) == {start}

        # Slice of a slice
        f = c.get_function_from_signature("nested(bytes)")
        first, second = _index_ranges(f)
        assert second.base == first.lvalue
        assert is_dependent(second.lvalue, start, f)
        assert is_dependent(second.lvalue, end, f)

        # Ternary operator in the bounds
        f = c.get_function_from_signature("ternary(bytes,bool)")
        assert {ir.start for ir in _index_ranges(f)} == {start, other}
        assert set(f.state_variables_read) == {start, other}

        # Array slice assigned to a local variable is an assignment, not an array initialization
        f = c.get_function_from_signature("arraySlice(uint256[])")
        (slice_ir,) = _index_ranges(f)
        assert str(slice_ir.lvalue.type) == "uint256[]"
        irs = [ir for node in f.nodes for ir in node.irs]
        assert not any(isinstance(ir, InitArray) for ir in irs)
        assert any(isinstance(ir, Assignment) and ir.rvalue == slice_ir.lvalue for ir in irs)
