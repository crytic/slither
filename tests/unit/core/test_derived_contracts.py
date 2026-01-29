"""
Tests for Contract.derived_contracts property.

Verifies that derived_contracts returns ALL contracts that inherit from self,
not just direct children. This is important for detectors like external_function
that need to find all overrides across the inheritance hierarchy.
"""

from pathlib import Path

from slither import Slither

TEST_DATA_DIR = Path(__file__).resolve().parent / "test_data" / "derived_contracts"


def test_derived_contracts_includes_all_descendants(solc_binary_path):
    """Test that derived_contracts returns all descendants, not just direct children.

    For inheritance: Base <- Child1 <- Grandchild
    Base.derived_contracts should return [Child1, Child2, Grandchild]
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    base = slither.get_contract_from_name("Base")[0]
    derived = base.derived_contracts
    derived_names = {c.name for c in derived}

    # Base should have Child1, Child2, AND Grandchild as derived contracts
    assert "Child1" in derived_names, "Child1 should be in Base.derived_contracts"
    assert "Child2" in derived_names, "Child2 should be in Base.derived_contracts"
    assert "Grandchild" in derived_names, (
        "Grandchild should be in Base.derived_contracts (indirect descendant)"
    )


def test_derived_contracts_direct_children(solc_binary_path):
    """Test that direct children are included in derived_contracts."""
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    child1 = slither.get_contract_from_name("Child1")[0]
    derived = child1.derived_contracts
    derived_names = {c.name for c in derived}

    # Child1's only derived contract is Grandchild
    assert "Grandchild" in derived_names


def test_derived_contracts_deep_chain(solc_binary_path):
    """Test derived_contracts with a deep inheritance chain: L1 <- L2 <- L3 <- L4.

    L1.derived_contracts should return [L2, L3, L4] - all descendants.
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    l1 = slither.get_contract_from_name("L1")[0]
    derived = l1.derived_contracts
    derived_names = {c.name for c in derived}

    assert "L2" in derived_names, "L2 should be in L1.derived_contracts"
    assert "L3" in derived_names, "L3 should be in L1.derived_contracts (2 levels deep)"
    assert "L4" in derived_names, "L4 should be in L1.derived_contracts (3 levels deep)"


def test_derived_contracts_no_descendants(solc_binary_path):
    """Test that contracts with no children return empty derived_contracts."""
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    standalone = slither.get_contract_from_name("Standalone")[0]
    assert standalone.derived_contracts == []

    grandchild = slither.get_contract_from_name("Grandchild")[0]
    assert grandchild.derived_contracts == []

    l4 = slither.get_contract_from_name("L4")[0]
    assert l4.derived_contracts == []


def test_derived_contracts_no_duplicates(solc_binary_path):
    """Test that derived_contracts doesn't contain duplicates.

    In diamond inheritance (Base <- Child1, Child2 <- Grandchild),
    Grandchild inherits Base through two paths, but should only appear once.
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    base = slither.get_contract_from_name("Base")[0]
    derived = base.derived_contracts
    derived_names = [c.name for c in derived]

    # Check no duplicates
    assert len(derived_names) == len(set(derived_names)), "derived_contracts has duplicates"


def test_immediate_vs_full_inheritance(solc_binary_path):
    """Verify the difference between immediate_inheritance and inheritance.

    This documents the expected behavior that derived_contracts uses the full
    inheritance chain, not just immediate parents.
    """
    solc_path = solc_binary_path("0.8.0")
    slither = Slither(Path(TEST_DATA_DIR, "derived_contracts.sol").as_posix(), solc=solc_path)

    grandchild = slither.get_contract_from_name("Grandchild")[0]

    # immediate_inheritance = direct parents only
    immediate_names = {c.name for c in grandchild.immediate_inheritance}
    assert immediate_names == {"Child1", "Child2"}

    # inheritance = full chain (C3 linearization)
    full_names = {c.name for c in grandchild.inheritance}
    assert "Base" in full_names, "Base should be in full inheritance chain"
    assert "Child1" in full_names
    assert "Child2" in full_names
