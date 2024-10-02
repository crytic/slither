pragma solidity 0.8.27;

/// Insufficient balance for transfer. Needed `required` but only
/// `available` available.
/// @param available balance available.
/// @param required requested amount to transfer.
error InsufficientBalance(uint256 available, uint256 required);

contract TestToken {
    mapping(address => uint) balance;
    function transferWithRequireError(address to, uint256 amount) public {
        require(
            balance[msg.sender] >= amount,
            InsufficientBalance(balance[msg.sender], amount)
        );
        balance[msg.sender] -= amount;
        balance[to] += amount;
    }
    // ...
}
