// pragma solidity ^0.5.0;

contract Uninitialized{

    address payable destination;

    function transfer() payable public{
        destination.transfer(msg.value);
    }

}


contract Test {
    mapping (address => uint) balances;
    mapping (address => uint) balancesInitialized;


    function init() public{
        balancesInitialized[msg.sender] = 0;
    }

    function use() view public{
        // random operation to use the mapping
        require(balances[msg.sender] == balancesInitialized[msg.sender]);
    }
}

library Lib{

    struct MyStruct{
        uint val;
    }

    function set(MyStruct storage st, uint v) public{
        st.val = v;
    }

}


contract Test2 {
    using Lib for Lib.MyStruct;

    Lib.MyStruct st;
    Lib.MyStruct stInitiliazed;
    uint v; // v is used as parameter of the lib, but is never init

    function init() public{
        stInitiliazed.set(v);
    }

    function use() view public{
        // random operation to use the structure
        require(st.val  == stInitiliazed.val);
    }

}
