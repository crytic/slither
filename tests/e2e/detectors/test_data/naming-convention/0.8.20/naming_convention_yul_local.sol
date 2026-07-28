// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/// Regression coverage for the `naming-convention` fix on Yul-local functions.
/// Inline assembly can declare local functions whose parameters are mangled by
/// the parser to `<source_name>__<scope_chain>`. The detector ran its
/// mixedCase regex on the mangled name and reported FPs.
/// After the fix, functions with non-empty `internal_scope` are skipped, so
/// neither the Yul function name nor its parameters are checked.
///
/// Expected output after fix: exactly one finding, for the deliberately
/// misnamed Solidity-level parameter `Bad_Param` (the tripwire that proves
/// the detector still flags regular Solidity-level violations).

library LibArr {
    function unsafeExtend(uint256[] memory base, uint256[] memory extend)
        internal
        pure
        returns (uint256[] memory)
    {
        assembly ("memory-safe") {
            function extendInline(base_, extend_) -> baseAfter_ {
                baseAfter_ := base_
                mstore(baseAfter_, add(mload(base_), mload(extend_)))
            }
            let res := extendInline(base, extend)
        }
        return base;
    }

    function copyBytes(bytes memory src) internal pure returns (bytes memory out) {
        out = new bytes(src.length);
        assembly ("memory-safe") {
            function memcpy(dst_, src_, len_) {
                for { let i := 0 } lt(i, len_) { i := add(i, 0x20) } {
                    mstore(add(dst_, i), mload(add(src_, i)))
                }
            }
            memcpy(add(out, 0x20), add(src, 0x20), mload(src))
        }
    }

    // Tripwire — a Solidity-level parameter using snake_case must still fire.
    function tripwire(uint256 Bad_Param) internal pure returns (uint256) {
        return Bad_Param;
    }
}
