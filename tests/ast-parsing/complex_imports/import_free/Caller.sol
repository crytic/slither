import "../FreeFuns.sol" as Free;

contract Caller {
    function foo(uint256 x) public pure returns (uint256) {
        return Free.foo(x);
    }

    function bar(uint256 x, uint256 y) public pure returns (uint256) {
        return Free.bar(x, y);
    }
}
