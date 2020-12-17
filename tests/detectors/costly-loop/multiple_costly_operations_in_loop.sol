pragma solidity ^0.4.24;

contract CostlyOperationsInLoop{
  
  uint loop_count = 100;                                                                                         
  uint state_variable=0;
  mapping (uint=>uint) map; 
  uint[100] arr;
  
  function bad() external{                                                                                      
    for (uint i=0; i < loop_count; i++){
      state_variable++;                                                                                    
    }                                                                                                        
  }

  function ignore_for_now1() external {
    for (uint i=0; i < 100; i++){
      map[i] = i+1;
    }
  }

  function ignore_for_now2() external {
    for (uint i=0; i < 100; i++){
      arr[i] = i+1;
    }
  }
  
  function good() external{
    uint local_variable = state_variable;
    for (uint i=0; i < loop_count; i++){
      local_variable++;                                                                                    
    }
    state_variable = local_variable;
  } 
}
