pragma solidity 0.8.18;

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