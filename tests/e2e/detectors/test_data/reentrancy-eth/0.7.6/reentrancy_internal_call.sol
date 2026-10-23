contract ReentrancyEthInternalCall {
    mapping(address => uint256) balances;

    function deposit() external payable {
        balances[msg.sender] += msg.value;
    }

    // Should be detected: the balance is read, then _send pays out before zeroing it
    function withdraw() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0);
        _send(amount);
    }

    // Should not be detected: the balance is zeroed before _pay sends ether
    function withdrawSafe() external {
        uint256 amount = balances[msg.sender];
        require(amount > 0);
        balances[msg.sender] = 0;
        _pay(amount);
    }

    function _send(uint256 amount) internal {
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
        balances[msg.sender] = 0;
    }

    function _pay(uint256 amount) internal {
        (bool success, ) = msg.sender.call{value: amount}("");
        require(success);
    }
}
