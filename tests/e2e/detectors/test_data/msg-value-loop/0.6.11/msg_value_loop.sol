contract C{

    mapping (address => uint256) balances;

    function bad(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            balances[receivers[i]] += msg.value;
        }
    }

    function bad2(address[] memory receivers) public payable { 
        for (uint256 i = 0; i < receivers.length; i++) {
            bad2_internal(receivers[i]);
        }
    }

    function bad2_internal(address a) internal {
        balances[a] += msg.value;
    }

    function bad3(address[] memory receivers) public payable { 
        for (uint256 i = 0; i < 2; i++) {
            for (uint256 j = 0; j < receivers.length; j++) {
                balances[receivers[j]] += msg.value;
            }
        }
    }

}