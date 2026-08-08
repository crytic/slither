// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract IncorrectMemorySafe {
    // BAD: Regular single-line comment - annotation will be ignored
    function badRegularComment() external pure returns (bytes32 result) {
        // @solidity memory-safe-assembly
        assembly {
            result := mload(0x40)
        }
    }

    // BAD: Regular multi-line comment - annotation will be ignored
    function badRegularMultiline() external pure returns (bytes32 result) {
        /* @solidity memory-safe-assembly */
        assembly {
            result := mload(0x40)
        }
    }

    // BAD: Typo - "sage" instead of "safe"
    function badTypoSage() external pure returns (bytes32 result) {
        /// @solidity memory-sage-assembly
        assembly {
            result := mload(0x40)
        }
    }

    // BAD: Typo - spaces instead of hyphens
    function badTypoSpaces() external pure returns (bytes32 result) {
        /// @solidity memory safe assembly
        assembly {
            result := mload(0x40)
        }
    }

    // BAD: Regular multi-line comment with continuation
    function badRegularMultilineContinuation() external pure returns (bytes32 result) {
        /*
         * @solidity memory-safe-assembly
         */
        assembly {
            result := mload(0x40)
        }
    }

    // GOOD: Correct NatSpec single-line comment
    function goodNatSpecSingle() external pure returns (bytes32 result) {
        /// @solidity memory-safe-assembly
        assembly {
            result := mload(0x40)
        }
    }

    // GOOD: Correct NatSpec multi-line comment (single line)
    function goodNatSpecMulti() external pure returns (bytes32 result) {
        /** @solidity memory-safe-assembly */
        assembly {
            result := mload(0x40)
        }
    }

    // GOOD: Correct NatSpec multi-line comment with continuation
    function goodNatSpecMultiContinuation() external pure returns (bytes32 result) {
        /**
         * @solidity memory-safe-assembly
         */
        assembly {
            result := mload(0x40)
        }
    }

    // GOOD: No annotation at all (not flagged)
    function goodNoAnnotation() external pure returns (bytes32 result) {
        assembly {
            result := mload(0x40)
        }
    }
}

// Test with modifier
contract ModifierTest {
    // BAD: Regular comment in modifier
    modifier checkSafe() {
        // @solidity memory-safe-assembly
        assembly {
            let x := mload(0x40)
        }
        _;
    }

    function useModifier() external checkSafe {}
}
