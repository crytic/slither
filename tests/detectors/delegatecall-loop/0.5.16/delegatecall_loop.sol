contract C{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
        }
    }

    function addBalance(address a) public payable {
        balances[a] += msg.value;
    }

}