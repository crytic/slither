pragma solidity 0.5.16;

// slither shouldn't throw "local variable never initialized" error on this file
// see https://github.com/crytic/slither/pull/1533

contract Test
{
    function f1() public view returns (int, string memory)  {
        return (0,"hello");
    }

    function f2(bool a) public view returns (string memory)  {
        if (a) {
            (int x, string memory z) = f1();
            return z;
        } else {
            (int x, string memory z) = f1();
            return z;
        }

    }
}
