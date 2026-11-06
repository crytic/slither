from slither.slithir.operations import Phi
from slither.slithir.variables import StateIRVariable


def test_entry_phis_preserve_shadowed_reads_and_write_only_state(slither_from_solidity_source):
    source = """
    pragma solidity ^0.8.19;
    contract A {
        uint private value;
        function readA() public view returns(uint) { return value; }
        function writeA(uint x) public { value = x; }
    }
    contract B is A {
        uint private value;
        uint private unused;
        function readB() public view returns(uint) { return value; }
        function writeB(uint x) public { value = x; unused = x; }
        function writeThenRead(uint x) public returns(uint) { value = x; return value; }
    }
    """
    with slither_from_solidity_source(source) as slither:
        contract = slither.get_contract_from_name("B")[0]
        for function in contract.functions:
            phis = [
                ir.lvalue.non_ssa_version
                for ir in function.entry_point.irs_ssa
                if isinstance(ir, Phi) and isinstance(ir.lvalue, StateIRVariable)
            ]
            if function.name in {"readA", "readB"}:
                assert [(v.name, v.contract.name) for v in phis] == [
                    ("value", "A" if function.name == "readA" else "B")
                ]
            elif function.name in {"writeA", "writeB", "writeThenRead"}:
                assert not phis


def test_call_phis_preserve_later_and_shadowed_state_reads(slither_from_solidity_source):
    from slither.slithir.operations import PhiCallback

    source = """
    pragma solidity ^0.8.19;
    contract A {
        uint private value;
        function a(address target) public returns(uint) { target.call(""); return value; }
        function setA(uint x) public { value = x; }
    }
    contract B is A {
        uint private value;
        uint private written;
        function setB(uint x) public { value = x; }
        function b(address target) public returns(uint) {
            target.call(""); written = 1; return value;
        }
    }
    """
    with slither_from_solidity_source(source) as slither:
        contract = slither.get_contract_from_name("B")[0]
        for name, owner in [("a", "A"), ("b", "B")]:
            function = next(f for f in contract.functions if f.name == name)
            phis = [ir for n in function.nodes for ir in n.irs_ssa if isinstance(ir, PhiCallback)]
            assert len(phis) == 1
            assert phis[0].lvalue.name == "value"
            assert phis[0].lvalue.contract.name == owner
