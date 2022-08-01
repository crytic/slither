type Fix is int192;


contract FixLib {
    function div(uint256 numerator, uint256 divisor) public pure returns (uint256) {
        return numerator / divisor;
    }
    function works(Fix x) external pure returns (uint256) {
        uint256 y = uint192(Fix.unwrap(x));
        return div(y, 1e18);
    }
    function test(Fix x) external pure returns (uint256) {
        return div(uint192(Fix.unwrap(x)), 1e18);
    }
}
