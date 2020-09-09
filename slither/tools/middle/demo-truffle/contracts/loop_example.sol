contract LoopExample {
    function fib(uint256 n) public returns (uint256 res) {
        uint256 prev_prev_num;
        uint256 prev_num = 0;
        uint256 num = 1;
        for (uint256 i = 1; i < n; i++) {
            prev_prev_num = prev_num;
            prev_num = num;
            num = prev_prev_num + prev_num;
        }
        return num;
    }
}
