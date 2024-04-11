from pathlib import Path
import pytest
from slither import Slither
from slither.core.declarations import Function, CustomErrorTopLevel, EventTopLevel
from slither.core.solidity_types.type_alias import TypeAliasTopLevel, TypeAliasContract
from slither.core.variables.top_level_variable import TopLevelVariable

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"
SRC_MAPPING_TEST_ROOT = Path(TEST_DATA_DIR, "src_mapping")

# Ensure issue fixed in https://github.com/crytic/crytic-compile/pull/554 does not regress in Slither's reference lookup.
@pytest.mark.parametrize("solc_version", ["0.6.12", "0.8.7", "0.8.8"])
def test_source_mapping_inheritance(solc_binary_path, solc_version):
    solc_path = solc_binary_path(solc_version)
    file = Path(SRC_MAPPING_TEST_ROOT, "inheritance.sol").as_posix()
    slither = Slither(file, solc=solc_path)

    # 3 reference to A in inheritance `contract $ is A`
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 9)} == {
        (121, 122),
        (185, 186),
        (299, 300),
    }

    # Check if A.f() is at the offset 27
    functions = slither.offset_to_objects(file, 27)
    assert len(functions) == 1
    function = functions.pop()
    assert isinstance(function, Function)
    assert function.canonical_name == "A.f()"

    # Only one definition for A.f()
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 27)} == {(26, 28)}
    # Only one reference for A.f(), in A.test()
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 27)} == {(92, 93)}
    # Three overridden implementation of A.f(), in A.test()
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 27)} == {
        (17, 53),
        (129, 166),
        (193, 230),
    }

    # Check if C.f() is at the offset 203
    functions = slither.offset_to_objects(file, 203)
    assert len(functions) == 1
    function = functions.pop()
    assert isinstance(function, Function)
    assert function.canonical_name == "C.f()"

    # Only one definition for C.f()
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 203)} == {(202, 204)}
    # Two references for C.f(), in A.test() and C.test2()
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 203)} == {
        (270, 271),
        (92, 93),
    }
    # Only one implementation for A.f(), in A.test()
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 203)} == {(193, 230)}

    # Offset 93 is the call to f() in A.test()
    # This can lead to three differents functions, depending on the current contract's context
    functions = slither.offset_to_objects(file, 93)
    print(functions)
    assert len(functions) == 3
    for function in functions:
        assert isinstance(function, Function)
        assert function.canonical_name in ["A.f()", "B.f()", "C.f()"]

    # There is one definition in the lexical scope of A
    assert {(x.start, x.end) for x in slither.offset_to_definitions(file, 93)} == {
        (26, 28),
    }

    # There are two references possible (in A.test() or C.test2() )
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 93)} == {
        (92, 93),
        (270, 271),
    }

    # There are three implementations possible (in A, B or C)
    assert {(x.start, x.end) for x in slither.offset_to_implementations(file, 93)} == {
        (17, 53),
        (193, 230),
        (129, 166),
    }


def _sort_references_lines(refs: list) -> list:
    return sorted([ref.lines[0] for ref in refs])


def test_references_user_defined_aliases(solc_binary_path):
    """
    Tests if references are filled correctly for user defined aliases (declared using "type [...] is [...]" statement).
    """
    solc_path = solc_binary_path("0.8.16")
    file = Path(SRC_MAPPING_TEST_ROOT, "ReferencesUserDefinedAliases.sol").as_posix()
    slither = Slither(file, solc=solc_path)

    alias_top_level = slither.compilation_units[0].type_aliases["aliasTopLevel"]
    assert len(alias_top_level.references) == 2
    lines = _sort_references_lines(alias_top_level.references)
    assert lines == [12, 16]

    alias_contract_level = (
        slither.compilation_units[0].contracts[0].file_scope.type_aliases["C.aliasContractLevel"]
    )
    assert len(alias_contract_level.references) == 2
    lines = _sort_references_lines(alias_contract_level.references)
    assert lines == [13, 16]


def test_references_user_defined_types_when_casting(solc_binary_path):
    """
    Tests if references are filled correctly for user defined types in case of casting.
    """
    solc_path = solc_binary_path("0.8.16")
    file = Path(SRC_MAPPING_TEST_ROOT, "ReferencesUserDefinedTypesCasting.sol").as_posix()
    slither = Slither(file, solc=solc_path)

    contracts = slither.compilation_units[0].contracts
    a = contracts[0] if contracts[0].is_interface else contracts[1]
    assert len(a.references) == 2
    lines = _sort_references_lines(a.references)
    assert lines == [12, 18]


def test_source_mapping_top_level_defs(solc_binary_path):
    solc_path = solc_binary_path("0.8.24")
    file = Path(SRC_MAPPING_TEST_ROOT, "TopLevelReferences.sol").as_posix()
    slither = Slither(file, solc=solc_path)

    # Check if T is at the offset 5
    types = slither.offset_to_objects(file, 5)
    assert len(types) == 1
    type_ = types.pop()
    assert isinstance(type_, TypeAliasTopLevel)
    assert type_.name == "T"

    assert {(x.start, x.end) for x in slither.offset_to_references(file, 5)} == {
        (48, 49),
        (60, 61),
        (134, 135),
        (140, 141),
        (163, 164),
    }

    # Check if U is at the offset 33
    constants = slither.offset_to_objects(file, 33)
    assert len(constants) == 1
    constant = constants.pop()
    assert isinstance(constant, TopLevelVariable)
    assert constant.name == "U"
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 33)} == {(147, 148)}

    # Check if V is at the offset 46
    errors = slither.offset_to_objects(file, 46)
    assert len(errors) == 1
    error = errors.pop()
    assert isinstance(error, CustomErrorTopLevel)
    assert error.name == "V"
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 46)} == {(202, 203)}

    # Check if W is at the offset 58
    events = slither.offset_to_objects(file, 58)
    assert len(events) == 1
    event = events.pop()
    assert isinstance(event, EventTopLevel)
    assert event.name == "W"
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 58)} == {(231, 232)}

    # Check if X is at the offset 87
    types = slither.offset_to_objects(file, 87)
    assert len(types) == 1
    type_ = types.pop()
    assert isinstance(type_, TypeAliasContract)
    assert type_.name == "X"
    assert {(x.start, x.end) for x in slither.offset_to_references(file, 87)} == {
        (245, 246),
        (251, 252),
    }


def test_references_self_identifier():
    """
    Tests that shadowing state variables with local variables does not affect references.
    """
    file = Path(SRC_MAPPING_TEST_ROOT, "SelfIdentifier.vy").as_posix()
    slither = Slither(file)

    contracts = slither.compilation_units[0].contracts
    a = contracts[0].state_variables[0]
    assert len(a.references) == 1
    lines = _sort_references_lines(a.references)
    assert lines == [4]
