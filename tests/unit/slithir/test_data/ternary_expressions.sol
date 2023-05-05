interface Test {
    function test() external payable returns (uint);
    function testTuple() external payable returns (uint, uint);
}
contract C {
    // TODO
    // 1) support variable declarations
    //uint min = 1 > 0 ? 1 : 2;
    // 2) suppory ternary index range access
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
    function g(address one) public {
        (, uint x) = Test(one).testTuple();
    }
    
    uint[] myIntegers;
    function _h(uint c) internal returns(uint) {
        return c;
    }
    function h(bool cond, uint a, uint b) public {
        uint d = _h(
            myIntegers[cond ? a : b]
        );
    }
    
    function i(bool cond) public {
        bytes memory a = new bytes(cond ? 1 : 2);
    }
}
