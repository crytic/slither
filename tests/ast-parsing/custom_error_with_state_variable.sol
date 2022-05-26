// This test check our custom error lookup
// Which require a strict order of logic
// As _find_top_level require custom error
// To be parsed when they the function reaches
// the custom error lookup
// See https://github.com/crytic/slither/issues/1115

error ErrorWithParam(uint256 value);
uint256 constant ONE = 1;
uint256 constant TWO = ONE + 1;
function foo() pure { revert ErrorWithParam(0); }
contract Bar { }

