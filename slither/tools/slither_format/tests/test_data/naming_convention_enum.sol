pragma solidity ^0.4.24;

contract A {

  /*  enum definition - bad */
  enum e {ONE, TWO}

  /* enum declaration - bad */
  e e1;
  
  function foo() {
    /* enum use - bad */
    e1 = e.ONE;
  }
}

contract B {

  /* enum definition - good */
  enum E {ONE, TWO}

  /* enum definition - good */
  E e1;
  
  function foo() {
    /* enum use - good */
    e1 = E.ONE;
  }
  
}

contract C {

  /* enum definition - bad */
  enum e {ONE, TWO}

  /* enum declaration - bad */
  e e1;

  /* enum as parameter and return value - bad */
  function foo(e eA) returns (e) {
    e e2 = eA;
    return (e2);
  }
}

contract D is C {
  /* enum as parameter and return value - bad */
  function foo(e eA) returns (e) {
    e e2 = eA;
    return (e2);
  }
}
