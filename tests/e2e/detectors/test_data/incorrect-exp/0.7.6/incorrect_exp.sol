contract Test {

    uint my_var = 2 ^ 256-1;

    function bad0(uint a) internal returns (uint) {
      return a^2;
    }

    function bad1() internal returns (uint) {
      uint UINT_MAX = 2^256-1;
      return UINT_MAX;
    }

    /* Correct exponentiation operator */
    function good0(uint a) internal returns (uint) {
      return a**2;
    }

    /* Neither operand is a constant */
    function good1(uint a) internal returns (uint) {
      return a^a;
    }

    /* The constant operand 0xff in hex typically means bitwise xor */
    function good2(uint a) internal returns (uint) {
      return a^0xff;
    }
}

contract Derived is Test {}
