// SPDX-License-Identifier: MIT
pragma solidity 0.8.20;

/// Regression coverage for the `incorrect-modifier` fix.
/// `if (cond) { _; } else { revert(...); }` is the structural pattern that
/// exercises the detector's `_get_false_son` walker — the walker descends into
/// the false branch and asks `is_revert(node)`. The kill-set inside `is_revert`
/// must therefore recognise every form of `revert` to avoid an FP on the four
/// "ok*" modifiers below. Only `brokenNoReturn` should be reported.
contract C {
    address owner;
    error NotOwner();
    error NotAuthorised(address caller);

    // negative case — falls off the end without reverting (genuine TP).
    modifier brokenNoReturn() {
        if (msg.sender == owner) {
            _;
        }
        // no else, no revert at end -> default zero/false leaks out.
    }

    // existing case — `revert()` was already recognised pre-fix.
    modifier okBareRevert() {
        if (msg.sender == owner) {
            _;
        } else {
            revert();
        }
    }

    // FP class #1 (fix): `revert("string")` -> SolidityFunction("revert(string)").
    modifier okStringRevert() {
        if (msg.sender == owner) {
            _;
        } else {
            revert("not owner");
        }
    }

    // FP class #2 (fix): custom-error revert, no args -> SolidityCustomRevert("revert NotOwner()").
    modifier okCustomError() {
        if (msg.sender == owner) {
            _;
        } else {
            revert NotOwner();
        }
    }

    // FP class #3 (fix): custom-error revert, with args.
    modifier okCustomErrorArgs() {
        if (msg.sender == owner) {
            _;
        } else {
            revert NotAuthorised(msg.sender);
        }
    }

    function f1() external okBareRevert      returns (uint256) { return 1; }
    function f2() external okStringRevert    returns (uint256) { return 2; }
    function f3() external okCustomError     returns (uint256) { return 3; }
    function f4() external okCustomErrorArgs returns (uint256) { return 4; }
    function f5() external brokenNoReturn    returns (uint256) { return 5; }
}
