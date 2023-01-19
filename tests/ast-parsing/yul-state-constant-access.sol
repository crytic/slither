contract A{
	uint private constant a = 10;

	function f() public returns(uint){
		return a;
	}

	function f2() public returns(uint){
		uint ret;
		assembly{
			ret := a
		}
	}

	function f3() public returns(uint){
		uint ret;
		unchecked{
			ret = a;
		}
	}
}

contract B is A{

}