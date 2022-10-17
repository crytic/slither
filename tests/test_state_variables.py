"""
tests for `slither.core.declarations.Contract`.
tests that `tests/test_state_variables.sol` instantiates
contract with correct state variables
"""
import collections
from solc_select import solc_select
from slither import Slither
from slither.core.solidity_types import ElementaryType, ArrayType
from slither.core.expressions import Literal


solc_select.switch_global_version("0.8.4", always_install=True)
slither = Slither("tests/test_state_variables.sol")
base = slither.get_contract_from_name("BaseContract")[0]
derived = slither.get_contract_from_name("DerivedContract")[0]


def test_state_variable_properties():
    base_vars = base.variables_as_dict

    one = base_vars["one"]
    assert one.name == "one", "wrong name"
    assert one.canonical_name == "BaseContract.one", "wrong canonical_name"
    assert one.type == ElementaryType("uint256"), "wrong type"
    assert one.visibility == "public", "wrong visibility"

    base_gap = base_vars["__gap"]
    assert base_gap.name == "__gap", "wrong name"
    assert base_gap.canonical_name == "BaseContract.__gap", "wrong canonical_name"
    assert base_gap.type == ArrayType(
        ElementaryType("uint256"), Literal("50", ElementaryType("uint256"))
    ), "wrong type"
    assert base_gap.visibility == "private", "wrong visibility"

    two = base_vars["two"]
    assert two.name == "two", "wrong name"
    assert two.canonical_name == "BaseContract.two", "wrong canonical_name"
    assert two.type == ElementaryType("uint256"), "wrong type"
    assert two.visibility == "internal", "wrong visibility"

    derived_vars = derived.variables_as_dict

    three = derived_vars["three"]
    assert three.name == "three", "wrong name"
    assert three.canonical_name == "DerivedContract.three", "wrong canonical_name"
    assert three.type == ElementaryType("uint256"), "wrong type"
    assert three.visibility == "public", "wrong visibility"

    derived_gap = derived_vars["__gap"]
    assert derived_gap.name == "__gap", "wrong name"
    assert derived_gap.canonical_name == "DerivedContract.__gap", "wrong canonical_name"
    assert derived_gap.type == ArrayType(
        ElementaryType("uint256"), Literal("50", ElementaryType("uint256"))
    ), "wrong type"
    assert derived_gap.visibility == "private", "wrong visibility"

    four = derived_vars["four"]
    assert four.name == "four", "wrong name"
    assert four.canonical_name == "DerivedContract.four", "wrong canonical_name"
    assert four.type == ElementaryType("uint256"), "wrong type"
    assert four.visibility == "internal", "wrong visibility"


# check whether lists with duplicate, unsorted items are equal
compare = lambda x, y: collections.Counter(x) == collections.Counter(y)


def test_contract_state_variable_getters():
    # the base contract should declare all variables which the derived inherits
    assert compare(base.state_variables_declared, derived.state_variables_inherited)
    # the base contract should not inherit any variables (no inheritance)
    assert base.state_variables_inherited == []
    # the derived state variables should be the aggregate of the declared and inherited
    assert compare(
        derived.state_variables,
        derived.state_variables_declared + derived.state_variables_inherited,
    )
    # the entry points should be all state variables filtered for only publicly visible variables
    assert compare(
        derived.state_variables_entry_points,
        list(filter(lambda x: x.visibility == "public", derived.state_variables)),
    )
