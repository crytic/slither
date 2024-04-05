// SPDX-License-Identifier: MIT
pragma solidity ^0.6.11;

contract DOSVulnerableContract {
	
     struct User {
        uint256 id;
        string name;
    }
    
    // Function that contains an infinite loop
    function infiniteLoop() external {
        while (true) {
            // This loop runs indefinitely, consuming all available gas
        }
    

    mapping(uint256 => User) public users;

    function addUser(uint256 _id, string memory _name) public {
        users[_id] = User(_id, _name);
    }

    function getUser(uint256 _id) public view returns (uint256, string memory) {
        User memory user = users[_id];
        return (user.id, user.name);
    }

    function updateUserName(uint256 _id, string memory _newName) public {
        User storage user = users[_id];
        user.name = _newName; // This modifies the state variable 'users'
    }
    // Function to perform a complex computation
    function performComplexComputation(uint256 n) external pure returns (uint256) {
        // This function performs a complex computation that depends on the input parameter 'n'
        uint256 result = 1;
        for (uint256 i = 1; i <= n; i++) {
            result *= i;
        }
        return result;
    }

    // Function to trigger a potential DOS attack
    function triggerDOS(uint256 n) external {
        // Call the performComplexComputation function with a large value of 'n'
        performComplexComputation(n);
    }mapping(address => uint256) public balances;

    // Function to deposit funds into the contract
    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // Function to withdraw funds from the contract
    function withdraw(uint256 amount) external {
        require(balances[msg.sender] >= amount, "Insufficient balance");
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success, "Transfer failed");
        balances[msg.sender] -= amount;
    }

    // Function to trigger a potential DOS attack
    function triggerDOS() external {
        // This loop consumes a large amount of gas
        for (uint256 i = 0; i < 100000; i++) {
            // Some computation that consumes gas
            uint256 x = i * 2;
        }
    }
    
    
}
