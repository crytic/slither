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

    function good1(address[] memory receivers) public payable {
        require(msg.value == 0);
        for (uint256 i = 0; i < receivers.length; i++) {
            balances[receivers[i]] += 1;
        }
    }

    function good2(address[] memory receivers) public payable {
        uint zero = 0;
        for (uint256 i = 0; i < receivers.length; i++) {
            assert(msg.value == zero);
            balances[receivers[i]] += 1;
        }
    }

    function good3(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            if (0 != msg.value) {
                revert();
            }
            balances[receivers[i]] += 1;
        }
    }

    function good4(address[] memory receivers) public payable {
        for (uint256 i = 0; i < receivers.length; i++) {
            _g();
            balances[receivers[i]] += 1;
        }
    }

    function _g() internal {
        require(msg.value == 0);
    }
}