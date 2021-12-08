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

    function bad2(address[] memory receivers) public payable {
        bad2_internal(receivers);
    }

    function bad2_internal(address[] memory receivers) internal {
        for (uint256 i = 0; i < receivers.length; i++) {
            address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
        }
    }

    function bad3(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            for (uint256 j = 0; j < receivers.length; j++) {
                address(this).delegatecall(abi.encodeWithSignature("addBalance(address)", receivers[i]));
            }
        }
    }

}