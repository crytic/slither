contract A{
	uint private v = 10;
}

contract B{
	uint v = 20;
}

contract C is B, A{
	function f() public view returns(uint) {
		return v;
	}
}