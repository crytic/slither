contract C{

    address addr = 0x41;

    bytes4 func_id;

    function bad_delegate_call(bytes data){
        addr.delegatecall(data);
    }

    function set(bytes4 id){
        func_id = id;
    }

    function bad_delegate_call2(bytes data){
        addr.delegatecall(func_id, data);
    }

    function good_delegate_call(bytes data){
        addr.delegatecall(bytes4(0x41), data);
    }
}
