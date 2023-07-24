contract BinOp {
    uint a = 1 & 2;
    uint b = 1 ^ 2;
    uint c = 1 | 2;
    bool d = 2 < 1;
    bool e = 1 > 2;
    bool f = 1 <= 2;
    bool g = 1 >= 2;
    bool h = 1 == 2;
    bool i = 1 != 2;
    bool j = true && false;
    bool k = true || false;
    uint l = uint(1) - uint(2);
    bytes32 IMPLEMENTATION_SLOT = bytes32(uint256(keccak256('eip1967.proxy.implementation')) - 1);
    bytes2 m = "ab";
}       