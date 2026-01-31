"""Tests for super call resolution in diamond inheritance patterns.

Verifies that super calls in inherited functions are resolved based on the
inheriting contract's C3 linearization, not the declaring contract's linearization.
"""
from pathlib import Path

from slither import Slither
from slither.slithir.operations import InternalCall

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data"


def test_super_resolution_diamond_inheritance(solc_binary_path) -> None:
    """Test that super calls in inherited functions follow C3 linearization.

    Diamond pattern:
        A
       / \\
      B   C
       \\ /
        D

    C3 linearization for D: D -> C -> B -> A

    Expected super call targets in D's context:
    - D.setValue super -> C.setValue
    - C.setValue super -> B.setValue (NOT A!)
    - B.setValue super -> A.setValue
    """
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(TEST_DATA_DIR, "super_resolution_diamond.sol").as_posix(),
        solc=solc_path,
    )

    contract_d = slither.get_contract_from_name("DiamondD")[0]

    # Get all setValue functions in D's context
    set_value_funcs = {
        f.contract_declarer.name: f
        for f in contract_d.functions
        if f.name == "setValue"
    }

    # Verify D.setValue super -> C.setValue
    d_set_value = set_value_funcs["DiamondD"]
    d_internal_calls = [op for op in d_set_value.slithir_operations if isinstance(op, InternalCall)]
    assert len(d_internal_calls) == 1
    assert d_internal_calls[0].function.contract_declarer.name == "DiamondC", (
        f"D.setValue super should call C.setValue, got {d_internal_calls[0].function.contract_declarer.name}"
    )

    # Verify C.setValue (in D's context) super -> B.setValue
    c_set_value = set_value_funcs["DiamondC"]
    c_internal_calls = [op for op in c_set_value.slithir_operations if isinstance(op, InternalCall)]
    assert len(c_internal_calls) == 1
    assert c_internal_calls[0].function.contract_declarer.name == "DiamondB", (
        f"C.setValue super (in D's context) should call B.setValue, got "
        f"{c_internal_calls[0].function.contract_declarer.name}"
    )

    # Verify B.setValue (in D's context) super -> A.setValue
    b_set_value = set_value_funcs["DiamondB"]
    b_internal_calls = [op for op in b_set_value.slithir_operations if isinstance(op, InternalCall)]
    assert len(b_internal_calls) == 1
    assert b_internal_calls[0].function.contract_declarer.name == "DiamondA", (
        f"B.setValue super (in D's context) should call A.setValue, got "
        f"{b_internal_calls[0].function.contract_declarer.name}"
    )


def test_super_resolution_simple_inheritance(solc_binary_path) -> None:
    """Test that super calls work correctly in simple (non-diamond) inheritance.

    Verifies that the fix doesn't break the simple case where contract == contract_declarer.
    """
    solc_path = solc_binary_path("0.8.15")
    slither = Slither(
        Path(TEST_DATA_DIR, "super_resolution_diamond.sol").as_posix(),
        solc=solc_path,
    )

    # In C's own context (not inherited), super should go to A
    contract_c = slither.get_contract_from_name("DiamondC")[0]
    c_set_value = contract_c.get_function_from_signature("setValue(uint256)")
    c_internal_calls = [op for op in c_set_value.slithir_operations if isinstance(op, InternalCall)]

    assert len(c_internal_calls) == 1
    assert c_internal_calls[0].function.contract_declarer.name == "DiamondA", (
        f"C.setValue super (in C's own context) should call A.setValue, got "
        f"{c_internal_calls[0].function.contract_declarer.name}"
    )

    # In B's own context, super should go to A
    contract_b = slither.get_contract_from_name("DiamondB")[0]
    b_set_value = contract_b.get_function_from_signature("setValue(uint256)")
    b_internal_calls = [op for op in b_set_value.slithir_operations if isinstance(op, InternalCall)]

    assert len(b_internal_calls) == 1
    assert b_internal_calls[0].function.contract_declarer.name == "DiamondA", (
        f"B.setValue super (in B's own context) should call A.setValue, got "
        f"{b_internal_calls[0].function.contract_declarer.name}"
    )
