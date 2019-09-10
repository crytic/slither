pragma solidity ^0.4.24;

/* contract definitione */
contract one {
  /* contract declaration as state variable */
  three k; 

  function foo(uint i) {
    /* contract declaration as local variable */
    three l;
    l.foo(10);
    k.foo(10);
  }
}

/* contract definitione */
contract Two {
  /* contract declaration as state variable */
  one m;

  function foo() {
    /* contract declaration as local variable */
    one n;
    n.foo(10);
    m.foo(100);
  }
  
}

/* contract definitione */
contract three {
  /* contract declaration as state variable */
  Two o;

  /* contract as function return value */
  function foo(uint i) returns (one) {
    /* contract declaration as local variable */
    Two p;
    p.foo();
    o.foo();
    /* new contract object */
    one r = new one();
    return(r);
  }
  
  /* contract as function parameter */
  function foobar(one q) {
    q.foo(10);
  }
}

