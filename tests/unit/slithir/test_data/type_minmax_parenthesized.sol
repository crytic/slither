// SPDX-License-Identifier: GPL-3.0
pragma solidity ^0.8.0;

// Regression test for parenthesized `type(X).max` / `type(X).min`.
//
// `(type(uint8)).max` is parsed with the `type()` call wrapped in a
// single-element TupleExpression. The folding in `expression_to_slithir` must
// unwrap the redundant parentheses; otherwise the member access reaches
// `convert.py` and IR generation fails with "type(uint8).max is unknown".
contract C {
    function paren_max() external pure returns (uint8) {
        return (type(uint8)).max;
    }

    function paren_min() external pure returns (uint8) {
        return (type(uint8)).min;
    }

    function nested_paren_max() external pure returns (uint256) {
        return ((type(uint256))).max;
    }

    function signed_min() external pure returns (int256) {
        return (type(int256)).min;
    }

    // The non-parenthesized form must keep working.
    function plain_max() external pure returns (uint8) {
        return type(uint8).max;
    }
}
