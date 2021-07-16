pragma solidity 0.6.2;

//based on not-so-smart-contract  

contract Overflow {
    uint private sellerBalance=0;
    
  constructor() public{
      
  }
    
    function add(uint value) public returns (bool){
    //There are also integer overflow and underflow in Ethereum, and it will not throw an exception when overflow and underflow occur. If the overflow (underflow) result is related to the amount of money, it may cause serious economic loss, so developers need to deal with integer overflow (underflow) manually. The common method is to use the SafeMath library for integer operation, or you can manually check the result after integer operation.
        sellerBalance += value; 
    } 
}
