pragma solidity ^0.4.24;

contract One {
  /* event declaration - bad */
  event e(uint); 

  function foo(uint i) {
    /* event call - bad */
    e(i);
  }
}

contract Two {
  /* event declaration - good */
  event E(uint);

  function foo(uint i) {
    /* event call - good */
    E(i);
  }
  
}

contract Three {
  /* event declaration - bad */
  event e(uint);

  function foo(uint i) {
    /* event call with emit - bad */
    emit e(i);
  }  

}

contract Four is Three {
  function foo(uint i) {
    /* event call with emit - bad */
    emit e(i);
  }  
}
