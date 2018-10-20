pragma solidity ^0.4.24;

contract Uninitialized{

    address destination;

    function transfer() payable public{
        destination.transfer(msg.value);
    }

}


contract Test {
    mapping (address => uint) balances;
    mapping (address => uint) balancesInitialized;


    function init() {
        balancesInitialized[msg.sender] = 0;
    }

    function use() {
        // random operation to use the mapping
        require(balances[msg.sender] == balancesInitialized[msg.sender]);
    }
}

library Lib{

    struct MyStruct{
        uint val;
    }

    function set(MyStruct storage st){
        st.val = 4;
    }

}


contract Test2 {
    using Lib for Lib.MyStruct;

    Lib.MyStruct st;
    Lib.MyStruct stInitiliazed;

    function init(){
        stInitiliazed.set();
    }

    function use(){
        // random operation to use the structure
        require(st.val  == stInitiliazed.val);
    }

}