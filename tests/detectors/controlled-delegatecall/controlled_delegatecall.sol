contract C{

    address addr_good = address(0x41);
    address addr_bad ;

    bytes4 func_id;

    function bad_delegate_call(bytes memory data) public{
        addr_good.delegatecall(data);
        addr_bad.delegatecall(data);
    }

    function set(bytes4 id) public{
        func_id = id;
        addr_bad = msg.sender;
    }

    function bad_delegate_call2(bytes memory data) public{
        addr_bad.delegatecall(abi.encode(func_id, data));
    }

    function good_delegate_call(bytes memory data) public{
        addr_good.delegatecall(abi.encode(bytes4(""), data));
    }
}
