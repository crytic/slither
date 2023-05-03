abstract contract A{
	modifier m() virtual;

	function f() public m(){
        uint i = 1;
	}
}

contract C {
    modifier onePlaceholder() {
        _;
    }

    modifier multiplePlaceholders() {
        _;
        _;
        _;
    }

    modifier acceptsVar(uint a) {
        _;
    }

    modifier noParams {
        _;
    }
}
