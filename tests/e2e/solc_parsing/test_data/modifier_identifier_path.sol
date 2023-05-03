contract A{

	function f() public m {
		uint i = 1;
	}
	modifier m()virtual {_;}

}

contract B is A{

	modifier m() override {_;}

}
