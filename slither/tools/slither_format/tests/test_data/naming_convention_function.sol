pragma solidity ^0.4.24;

contract A {

  /* function definition - bad */
  function Foo() {
    /* function call - bad */
    uint i = Foobar(10);
  }

  /* function definition - bad */
  function Foobar(uint i) returns (uint) {
    return (1+10);
  }
  
}

contract B {
  /* function definition - good */
  function foo() {
    /* function call - good */
    uint i = foobar(10);
  }

  /* function definition - good */
  function foobar(uint i) returns (uint) {
    A a;
    /* function call - bad */
    return (a.Foobar(10) + i);
  }
}


