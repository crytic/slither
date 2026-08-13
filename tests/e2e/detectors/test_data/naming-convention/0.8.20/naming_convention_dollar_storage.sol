// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/// Regression coverage for the `naming-convention` fix on the ERC-7201
/// namespaced-storage pointer name `$`.
///
/// `$` is a valid Solidity identifier and the de-facto convention for the
/// storage-struct pointer (OpenZeppelin upgradeable, Solady, ...). It carries
/// no letters to case, so the mixedCase checks must not flag it. Before the
/// fix, every `function f(SomeStorage storage $)` reported a `Parameter ... .$
/// is not in mixedCase` false positive (24+ on Solady alone).
///
/// Expected output after fix: exactly one finding, for the deliberately
/// snake_cased parameter `bad_param` (the tripwire proving the detector still
/// flags genuine Solidity-level violations).

library LibExample {
    struct BytesStorage {
        bytes32 _spacer;
    }

    // `$` is read here -> exercises `is_mixed_case` on the storage pointer.
    function length(BytesStorage storage $) internal view returns (uint256 result) {
        assembly {
            result := shr(224, sload($.slot))
        }
    }

    // `$` is unused here -> exercises `is_mixed_case_with_underscore`.
    function clear(BytesStorage storage $) internal {}

    // Tripwire: a snake_cased parameter must still be reported.
    function tripwire(uint256 bad_param) internal pure returns (uint256) {
        return bad_param;
    }
}
