contract C {
    function returnConstant() public returns (uint) {
        return 0;
    }

    function returnVariable() public returns (uint) {
        uint x = 0;
        return x;
    }

    function returnTuple() public returns (uint, uint) {
        uint x = 0;
        uint y = 0;
        return (x, y);
    }

    function returnTernary() public returns (uint) {
        uint x = 0;
        return x == 0 ? 1 : 2;
    }

    mapping(uint => uint) m;

    function returnDelete() public {
        return delete(m[0]);
    }
}