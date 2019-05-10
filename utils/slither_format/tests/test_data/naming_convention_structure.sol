pragma solidity ^0.4.24;
pragma experimental ABIEncoderV2;

contract A {

  /* struct definition - bad */
  struct s {
    uint i;
  }

  /* struct declaration - bad */
  s s1;
  
  function foo() {
    s1.i = 10;
  }
}

contract B {

  /* struct definition - good */
  struct S {
    uint i;
  }

  /* struct definition - good */
  S s1;
  
  function foo() {
    s1.i = 10;
  }
  
}

contract C {

  /* struct definition - bad */
  struct s {
    uint i;
  }

  /* struct declaration - bad */
  s s1;

  /* struct as parameter and return value - bad */
  function foo(s sA) returns (s) {
    s1.i = sA.i;
    return (s1);
  }
}

