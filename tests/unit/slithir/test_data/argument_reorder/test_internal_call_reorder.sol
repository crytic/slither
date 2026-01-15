contract InternalCallReorderTest {
    function internal_func(uint256 a, bool b, uint256 c) internal {
    }

    function caller() external {
        internal_func({a: 3, c: 5, b: true});
    }
}
