pragma solidity >=0.4.24 <0.5.4;

contract Test {
   
  function foo() public returns (address) {
    address from = msg.sender;
    return(from);
  }
}
