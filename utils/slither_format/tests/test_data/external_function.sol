//pragma solidity ^0.4.24;

import "./external_function_import.sol";

contract ContractWithFunctionCalledSuper is ContractWithFunctionCalled {
    function callWithSuper() public {
        uint256 i = 0;
    }
}

contract ContractWithFunctionNotCalled {

  modifier mod (uint c) {
    require (c > 0);
    _;
  }

  // With parameter and return
  function funcNotCalled5(uint _i)
    public returns (uint) {
    return(_i + 10);
  }

  // With no visibility specifier which is ok until solc 0.5.0
  function funcNotCalled4() {
  }
  
  function funcNotCalled3() public
    returns (uint a)
  {
    a = 100;
  }
  
  function funcNotCalled2() public {
  }
  
  function funcNotCalled() public {
  }
  
  function my_func() internal returns(bool) {
    return true;
  }

  /* Cannot be converted to external because parameter i is written to in function and so cannot be in calldata */
  function test4(uint i) public returns(uint){
    i += 1;
    return(i);
  }

  /* public with modifier */
  function test5(uint number) public mod (number) returns(uint){
    return(number);
  }

  /* implicit with modifier */
  function test6(uint number) mod (number) returns(uint){
    return(number);
  }

}

contract ContractWithFunctionNotCalled2 is ContractWithFunctionCalledSuper {
    function funcNotCalled() public {
        uint256 i = 0;
        address three = address(new ContractWithFunctionNotCalled());
        three.call(abi.encode(bytes4(keccak256("helloTwo()"))));
        super.callWithSuper();
        ContractWithFunctionCalled c = new ContractWithFunctionCalled();
        c.funcCalled();
    }
}

contract InternalCall {
    
    function() returns(uint) ptr;
    
    function set_test1() external{
        ptr = test1;
    }
    
    function set_test2() external{
        ptr = test2;
    }
    
    function test1() public returns(uint){
        return 1;
    }
    
    function test2() public returns(uint){
        return 2;
    }
    
    function test3() public returns(uint){
        return 3;
    }
    
    function exec() external returns(uint){
        return ptr();
    }

}
