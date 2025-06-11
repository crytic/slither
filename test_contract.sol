
pragma solidity ^0.8.0;

contract VulnerableContract {
    uint256 public balance;
    mapping(address => uint256) public userBalances;
    
    event Deposit(address user, uint256 amount);
    event Withdrawal(address user, uint256 amount);
    
    function deposit() external payable {
        userBalances[msg.sender] += msg.value;
        balance += msg.value;
        emit Deposit(msg.sender, msg.value);
    }
    
    function withdraw(uint256 amount) external {
        require(userBalances[msg.sender] >= amount, "Insufficient balance");
        
        // Vulnerable: external call before state update
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        
        userBalances[msg.sender] -= amount;
        balance -= amount;
        emit Withdrawal(msg.sender, amount);
    }
    
    function internalHelper() internal {
        balance = balance * 2;
    }
    
    function complexFunction() external {
        internalHelper();
        balance += 100;
        emit Deposit(address(this), 100);
    }
}
