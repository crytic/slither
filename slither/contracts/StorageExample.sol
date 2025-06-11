pragma solidity ^0.8.0;

contract StorageExample {
    uint256 public balance;
    mapping(address => uint256) public balances;
    bool private locked;
    
    event Transfer(address indexed from, address indexed to, uint256 amount);
    
    function deposit() external payable {
        // Writes to storage
        balance += msg.value;
        balances[msg.sender] += msg.value;
    }
    
    function withdraw(uint256 amount) external {
        // Reads from storage  
        require(balances[msg.sender] >= amount, "Insufficient balance");
        require(!locked, "Reentrant call");
        
        // Writes to storage
        locked = true;
        balances[msg.sender] -= amount;
        
        // External call - potential reentrancy point
        payable(msg.sender).call{value: amount}("");
        
        // Writes to storage
        balance -= amount;
        locked = false;
        
        // Event emission
        emit Transfer(address(this), msg.sender, amount);
    }
    
    function getBalance(address user) external view returns (uint256) {
        // Reads from storage
        return balances[user];
    }
    
    function internalHelper() internal {
        // Reads from storage
        balance; // Access storage variable
    }
    
    function callInternal() external {
        internalHelper();
    }
} 