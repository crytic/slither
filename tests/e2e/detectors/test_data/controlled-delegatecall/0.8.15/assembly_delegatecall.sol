contract C{

    address addr_good = address(0x41);
    address addr_bad ;

    function set() public{
        addr_bad = msg.sender;
    }

    function bad_delegate_call() public{
        address target = addr_bad;
        assembly {
            let success := delegatecall(gas(), target, 0, 0, 0, 0)
        }
    }

    function bad_callcode() public{
        address target = addr_bad;
        assembly {
            let success := callcode(gas(), target, 0, 0, 0, 0, 0)
        }
    }

    function good_delegate_call() public{
        address target = addr_good;
        assembly {
            let success := delegatecall(gas(), target, 0, 0, 0, 0)
        }
    }
}
