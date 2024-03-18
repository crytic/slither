pragma solidity ^0.8.13;

contract Other {
    struct S {
        uint z;
        uint b;
        uint c;
        uint d;
    }

    mapping(uint => S) public M;
}

contract TestEmptyComponent {
    Other other;

    function test() external {
        (uint z, , uint c, uint d) = other.M(3);
    }
}

contract TestTupleReassign {
    function threeRet(int z) internal returns(int, int, int) {
        return (1,2,3);
    }
    function twoRet(int z) internal returns(int, int) {
        return (3,4);
    }

    function test() external returns(int) {
        (int a, int b, int c) = threeRet(3);
        (a, c) = twoRet(b);
        return b;
    }
}
