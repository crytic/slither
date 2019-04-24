pragma solidity ^0.4.24;

contract A {

  modifier one() {
    _;
  }

  function foo() one {
  }
}

contract B {

  modifier One() {
    _;
  }
  
  function foo () One {
  }

}

contract C {

  modifier one() {
    _;
  }

  modifier Two() {
    _;
  }

  function foo() one Two returns (uint) {
    uint One;
    return(One);
  }
  
}

