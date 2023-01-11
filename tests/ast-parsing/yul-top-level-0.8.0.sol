function top_level_yul(int256 c) pure returns (uint result) {
    assembly {
        function internal_yul(a) -> b {
            b := a
        }

        result := internal_yul(c)
    }
}


contract Test {
	function test() public{
		top_level_yul(10);
	}
}