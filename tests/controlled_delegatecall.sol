contract C{

    address addr_good = 0x41;
    address addr_bad ;

    bytes4 func_id;

    function bad_delegate_call(bytes data){
        addr_good.delegatecall(data);
        addr_bad.delegatecall(data);
    }

    function set(bytes4 id){
        func_id = id;
        addr_bad = msg.sender;
    }

    function bad_delegate_call2(bytes data){
        addr_bad.delegatecall(func_id, data);
    }

    function good_delegate_call(bytes data){
        addr_good.delegatecall(bytes4(0x41), data);
    }
}
