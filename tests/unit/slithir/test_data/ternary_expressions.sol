interface Test {
    function test() external payable returns (uint);
    function testTuple(uint) external payable returns (uint, uint);
}
contract C {
    // TODO
    // 1) support variable declarations
    //uint min = 1 > 0 ? 1 : 2;
    // 2) support ternary index range access
    // function e(bool cond, bytes calldata x) external {
    //     bytes memory a = x[cond ? 1 : 2 :];
    // }
    function a(uint a, uint b) external {
        (uint min, uint max) = a < b ? (a, b) : (b, a);
    }
    function b( address a, address b) external {
        (address tokenA, address tokenB) = a < b ? (a, b) : (b, a);
    }

    bytes char;
    function c(bytes memory strAddress, uint i, uint padding, uint length) external {
        char[0] = strAddress[i < padding + 2 ? i : 42 + i - length];
    }

    function d(bool cond, bytes calldata x) external {
        bytes1 a = x[cond ? 1 : 2];
    }

    function e(address one, address two) public {
        uint x = Test(one).test{value: msg.sender == two ? 1 : 2, gas: true ? 2 : gasleft()}();
    }

    // Parenthetical expression
    function f(address one, address two) public {
        uint x = Test(one).test{value: msg.sender == two ? 1 : 2, gas: true ? (1 == 1 ? 1 : 2) : gasleft()}();
    }

    // Unused tuple variable
    uint[] myIntegers;
    function g(address one, bool cond, uint a, uint b) public {
        (, uint x) = Test(one).testTuple(myIntegers[cond ? a : b]);
    }

    function h(bool cond) public {
        bytes memory a = new bytes(cond ? 1 : 2);
    }
}

contract D {
    function values(uint n) internal returns (uint, uint) {
        return (0, 1);
    }

    function a(uint n) external {
        uint a;
        (a,) = values(n > 0 ? 1 : 0);
    }
}
