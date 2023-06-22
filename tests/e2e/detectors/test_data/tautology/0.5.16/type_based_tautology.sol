contract A {
	function f(uint x) public returns (uint) {
        if (x >= 0) { // bad -- always true
            return 1;
        }
		return 7;
	}

	function g(uint8 y) public returns (bool) {
        return (y < 512); // bad!
	}
}