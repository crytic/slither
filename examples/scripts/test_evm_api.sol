pragma solidity >=0.4.24 <0.5.4;

contract Test {

  address owner;
  
  constructor () public {
    owner = msg.sender;
  }
  
  function foo() public returns (uint) {
    uint i;
    return(i+10);
  }

  function foobar(uint i) public returns (uint) {
    return(i+10);
  }
}
