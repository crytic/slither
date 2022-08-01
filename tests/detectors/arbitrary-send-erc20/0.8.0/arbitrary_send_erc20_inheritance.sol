pragma solidity 0.8.0;

library Safe {
 function safeTransferFrom(address token, address from, address to, uint256 amount) internal {}
}

contract T {
 using Safe for address;
 address erc20;
  
 function bad(address from) public {
  erc20.safeTransferFrom(from, address(0x1), 90);
 } 
}  
 
contract A is T {}
