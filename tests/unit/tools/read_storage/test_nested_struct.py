"""
Tests for nested struct support in slither-read-storage.

A struct member that is itself a struct must have its own members resolved
recursively, following Solidity's storage layout rules (a nested struct occupies
consecutive slots starting at the parent member's slot).

Related to issue #2077.
"""

import os
import tempfile

from slither import Slither
from slither.tools.read_storage.read_storage import SlitherReadStorage


def test_nested_struct_members(solc_binary_path) -> None:
    """Members of a struct nested inside another struct get their own slots."""
    solc_path = solc_binary_path("0.8.10")

    test_content = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract TestNestedStruct {
    struct Inner {
        uint128 a;   // slot base+0, offset 0
        uint128 b;   // slot base+0, offset 128 (packed with a)
        uint256 c;   // slot base+1
    }

    struct Middle {
        uint256 x;   // slot base+0
        Inner inner; // slot base+1 .. base+2
        uint256 y;   // slot base+3
    }

    struct Outer {
        uint256 p;     // slot 0
        Middle middle; // slot 1 .. 4
        uint256 q;     // slot 5
    }

    Outer private outer;
}
"""

    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_nested_struct.sol")
        with open(test_file, "w") as f:
            f.write(test_content)

        slither = Slither(test_file, solc=solc_path)
        contracts = slither.contracts

        srs = SlitherReadStorage(contracts, 20)
        srs.get_all_storage_variables()
        srs.get_storage_layout()

        assert "outer" in srs.slot_info, "Expected outer in slot_info"
        outer = srs.slot_info["outer"]
        assert outer.slot == 0, f"Expected outer at slot 0, got {outer.slot}"

        # Top-level members
        assert outer.elems["p"].slot == 0, f"Expected p at slot 0, got {outer.elems['p'].slot}"
        assert outer.elems["middle"].slot == 1, (
            f"Expected middle at slot 1, got {outer.elems['middle'].slot}"
        )
        assert outer.elems["q"].slot == 5, f"Expected q at slot 5, got {outer.elems['q'].slot}"

        # The nested struct's members must be resolved recursively.
        middle = outer.elems["middle"]
        assert middle.elems, "Expected nested struct 'middle' members to be resolved"
        assert middle.elems["x"].slot == 1, (
            f"Expected middle.x at slot 1, got {middle.elems['x'].slot}"
        )
        assert middle.elems["inner"].slot == 2, (
            f"Expected middle.inner at slot 2, got {middle.elems['inner'].slot}"
        )
        assert middle.elems["y"].slot == 4, (
            f"Expected middle.y at slot 4, got {middle.elems['y'].slot}"
        )

        # The doubly-nested struct's members must also be resolved, with correct
        # packing offsets relative to their own base slot.
        inner = middle.elems["inner"]
        assert inner.elems, "Expected doubly-nested struct 'inner' members to be resolved"
        assert inner.elems["a"].slot == 2, (
            f"Expected inner.a at slot 2, got {inner.elems['a'].slot}"
        )
        assert inner.elems["a"].offset == 0, (
            f"Expected inner.a offset 0, got {inner.elems['a'].offset}"
        )
        assert inner.elems["b"].slot == 2, (
            f"Expected inner.b at slot 2, got {inner.elems['b'].slot}"
        )
        assert inner.elems["b"].offset == 128, (
            f"Expected inner.b offset 128, got {inner.elems['b'].offset}"
        )
        assert inner.elems["c"].slot == 3, (
            f"Expected inner.c at slot 3, got {inner.elems['c'].slot}"
        )

        # Fully-qualified names should reflect the nesting path.
        assert inner.elems["a"].name == "outer.middle.inner.a", (
            f"Expected name 'outer.middle.inner.a', got {inner.elems['a'].name}"
        )
