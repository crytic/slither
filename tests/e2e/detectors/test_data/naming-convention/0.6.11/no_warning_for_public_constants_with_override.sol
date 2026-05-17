// Regression coverage for https://github.com/crytic/slither/issues/930
//
// A public constant that overrides an interface getter must NOT be flagged
// by the naming-convention detector for failing UPPER_CASE_WITH_UNDERSCORES.
// The behavior is already covered by the public-constant branch in
// slither/detectors/naming_convention/naming_convention.py, but the existing
// no_warning_for_public_constants.sol fixture does not exercise the `override`
// variant. This file locks that in.
interface I {
    function version() external view returns (uint256);
}

contract C is I {
    uint256 public constant override version = 1;
}
