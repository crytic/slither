pragma solidity 0.6.2;

//based on Osiris'paper

/*
A rare integer error is the truncation error, which occurs when a longer 
type is truncated to a shorter type, potentially resulting in a loss of 
accuracy.
*/

contract truncationError{
    mapping(address => uint32) public balances;
    
    constructor() public{
        
    }    
    
    function receiveEther() public payable{
        //truncation Error
        //In Solidity, a loss of accuracy may occur when a longer integer is cast to a shorter one.
        require(balances[msg.sender] + uint32(msg.value) >= balances[msg.sender]);
        balances[msg.sender] += uint32(msg.value);
        uint32 b = uint32(msg.value);
    }
}
