contract A{

	function f() public m {}
	modifier m()virtual {_;}

}

contract B is A{

	modifier m() override {_;}

}
