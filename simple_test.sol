
pragma solidity ^0.8.0;

contract SimpleTest {
    uint256 public balance;
    
    function vulnerable() external {
        uint256 userBalance = balance;  // Storage read
        msg.sender.call{value: userBalance}("");  // External call
        balance = 0;  // Storage write after call
    }
}
