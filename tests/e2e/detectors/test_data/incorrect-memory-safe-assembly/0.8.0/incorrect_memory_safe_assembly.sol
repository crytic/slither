// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// --- Should be flagged ---

contract RegularSingleLineComment {
    function f() external pure returns (uint256 result) {
        // @solidity memory-safe-assembly
        assembly {
            result := 42
        }
    }
}

contract RegularMultiLineComment {
    function f() external pure returns (uint256 result) {
        /* @solidity memory-safe-assembly */
        assembly {
            result := 42
        }
    }
}

contract TypoInNatSpec {
    function f() external pure returns (uint256 result) {
        /// @solidity memory-sage-assembly
        assembly {
            result := 42
        }
    }
}

// --- Should NOT be flagged ---

contract CorrectNatSpecSingleLine {
    function f() external pure returns (uint256 result) {
        /// @solidity memory-safe-assembly
        assembly {
            result := 42
        }
    }
}

contract CorrectNatSpecMultiLine {
    function f() external pure returns (uint256 result) {
        /** @solidity memory-safe-assembly */
        assembly {
            result := 42
        }
    }
}

contract NoAnnotation {
    function f() external pure returns (uint256 result) {
        assembly {
            result := 42
        }
    }
}

contract NoAssembly {
    function f() external pure returns (uint256) {
        return 42;
    }
}
