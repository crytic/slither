// pragma solidity ^0.5.0;

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
        (bool ret, bytes memory mem) = msg.sender.call{value:userBalance[msg.sender]}("");
        if( ! ret ){
            revert();
        }
        userBalance[msg.sender] = 0;
    }
    
    function withdrawBalance() public{
        // send userBalance[msg.sender] ethers to msg.sender
        // if mgs.sender is a contract, it will call its fallback function
        (bool ret, bytes memory mem) = msg.sender.call.value(userBalance[msg.sender])("");
        if( ! ret ){
            revert();
        }
        userBalance[msg.sender] = 0;
    }   

    function withdrawBalance_fixed() public{
        // To protect against re-entrancy, the state variable
        // has to be change before the call
        uint amount = userBalance[msg.sender];
        userBalance[msg.sender] = 0;
        (bool ret, bytes memory mem) = msg.sender.call.value(amount)("");
        if( ! ret ){
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
        (bool ret, bytes memory mem) = msg.sender.call.value(amount)("");
        if( ! ret ){
            userBalance[msg.sender] = amount;
        }
    }   
}
