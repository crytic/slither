pragma solidity ^0.4.24;

contract A {

  /* modifier definition - good */
  modifier one() {
    _;
  }
  
  /* modifier use - good */
  function foo() one {
  }
}

contract B {
  /* modifier definition - bad */
  modifier One() {
    _;
  }
  
  /* modifier use - bad */
  function foo () One {
  }

}

contract C {

  /* modifier definition - good */
  modifier one() {
    _;
  }
  
  /* modifier definition - bad */
  modifier Two() {
    _;
  }

  /* modifier uses - good and bad */
  function foo() one Two returns (uint) {
    /* Local variable with same name as bad modifier name from contract B */
    uint One;
    return(One);
  }
  
}

contract D is C {
  /* modifier uses - good and bad */
  function foo() one Two returns (uint) {
  }
}

