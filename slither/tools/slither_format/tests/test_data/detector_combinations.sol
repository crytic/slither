pragma solidity ^0.4.24;

contract A {

  /* constant state variable naming - bad */
  /* unused state variable - bad */
  /* Overlapping detectors - so neither will be applied for now */
  uint max_tx = 100;
  
  /* state variable declaration naming convention - bad */
  uint SV_count = 0;

  modifier mod (uint c) {
    require (c > 100);
    _;
  }

  /* parameter declaration naming convention - bad */
  function foo(uint Count) {
    /* parameter use naming convention- bad */
    /* state variable use naming convention - bad */
    SV_count = Count;
  }

  /* implicitly public, can be made external - bad */
  /* parameter declarations naming convention - bad */
  function foobar(uint Count, uint Number) returns (uint) {
    /* parameter use naming convention - bad */
    foo (Number);
    /* parameter use naming convention - bad */
    return (Count+Number);
  }

  /* explicitly public, can be made external - bad */
  /* view but modifies state - bad */
  /* parameter declarations naming convention - bad */
  /* parameter use passed to modifier naming convention - bad */
  function bar(uint Count) public view mod (Count) returns(uint) {
    /* Use of state variable naming convention - bad */
    /* Use of parameter naming convention - bad */
    SV_count += Count;
    /* Use of state variable naming convention - bad */
    return (SV_count);
  }

}


