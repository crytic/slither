pragma solidity ^0.4.24;

contract Reentrancy {
    mapping (address => uint) userBalance;
   
    function getBalance(address u) view public returns(uint){
        return userBalance[u];
    }

    function addToBalance() payable public{
        userBalance[msg.sender] += msg.value;
    }   

    // Should not detect reentrancy in constructor
    constructor() public {
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        if (!(msg.sender.call.value(userBalance[msg.sender])())) {
            revert();
        }
        userBalance[msg.sender] = 0;
    }

    function withdrawBalance() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        if( ! (msg.sender.call.value(userBalance[msg.sender])() ) ){
            revert();
        }
        userBalance[msg.sender] = 0;
    }   

    function withdrawBalance_fixed() public{
        // To protect against re-entrancy, the state variable
        // has to be change before the call
        uint amount = userBalance[msg.sender];
        userBalance[msg.sender] = 0;
        if( ! (msg.sender.call.value(amount)() ) ){
            revert();
        }
    }   

    function withdrawBalance_fixed_2() public{
        // send() and transfer() are safe against reentrancy
        // they do not transfer the remaining gas
        // and they give just enough gas to execute few instructions    
        // in the fallback function (no further call possible)
        msg.sender.transfer(userBalance[msg.sender]);
        userBalance[msg.sender] = 0;
    }   
   
    function withdrawBalance_fixed_3() public{
        // The state can be changed
        // But it is fine, as it can only occur if the transaction fails 
        uint amount = userBalance[msg.sender];
        userBalance[msg.sender] = 0;
        if( ! (msg.sender.call.value(amount)() ) ){
            userBalance[msg.sender] = amount;
        }
    }   
    function withdrawBalance_fixed_4() public{
        // The state can be changed
        // But it is fine, as it can only occur if the transaction fails 
        uint amount = userBalance[msg.sender];
        userBalance[msg.sender] = 0;
        if( (msg.sender.call.value(amount)() ) ){
            return;
        }
        else{
            userBalance[msg.sender] = amount;
        }
    }   

    function withdrawBalance_nested() public{
        uint amount = userBalance[msg.sender];
        if( ! (msg.sender.call.value(amount/2)() ) ){
            msg.sender.call.value(amount/2)();
            userBalance[msg.sender] = 0;
        }
    }   

}


contract Called{
    function f() public;
}

contract ReentrancyEvent {

    event E();

    function test(Called c) public{

        c.f();
        emit E();

    }
}

