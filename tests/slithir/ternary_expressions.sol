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
}
