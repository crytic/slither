pragma solidity ^0.8.0;

contract A {
    function add(uint256 a, uint256 b) public returns (uint256) {
        return a + b;
    }
}

contract B is A {
    function assignFunction() public {
        function(uint256, uint256) returns (uint256) myFunction = super.add;
    }
}