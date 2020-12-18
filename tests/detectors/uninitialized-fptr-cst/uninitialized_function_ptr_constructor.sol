pragma solidity 0.5.8;

contract bad0 {
  constructor() public {
    /* Uninitialized function pointer */
    function(uint256) internal returns(uint256) a;
    a(10);
  }
}

contract bad1 {
  constructor() public {
    /* Uninitialized function pointer but external visibility */
    /* Although the Solidity bug report does not specify external visibility, we believe both internal/external may be vulnerable */
    function(uint256) external returns(uint256) b;
    b(10);
  }
}

contract bad2 {
  struct S {
    /* Uninitialized function pointer within a struct*/
    function(uint256) internal returns(uint256) a;
  }
  constructor() public {
    S memory s;
    s.a(10);
  }
}

contract bad3 {
  /* Uninitialized state variable function pointer written-to after call */
  function(uint256) internal returns(uint256) a;

  constructor() public {
    a(10);
    a = foo;
  }
  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}

contract good0 {
  constructor() public {
    /* Uninitialized function pointer but not called */
    function(uint256) internal returns(uint256) a;
  }
}

contract good1 {
  constructor() public {
    /* Initialized function pointer */
    function(uint256) internal returns(uint256) a = foo;
    a(10);
  }
  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}

contract good2 {  
  constructor() public {
  }
  function foo(uint256 i) internal returns(uint256) {
    /* Uninitialized function pointer but not in constructor */
    function(uint256) internal returns(uint256) a;
    a(10);
    return(i);
  } 
}

contract good3 {
  constructor() public {
    /* Normal function call */
    foo(10);
  }
  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}

contract good4 {
  struct S {
    uint S_i;
  }
  constructor() public {
    /* Uninitialized variables of other types but not function pointer */
    uint i;
    address addr;
    uint[] memory arr;
    S memory s;
  }
}

contract good5 {
  constructor() public {
    /* Uninitialized local function pointer written to later */
    function(uint256) internal returns(uint256) a;
    a = foo;
    a(10);
  }
  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}

contract good6 {
  /* Uninitialized state variable function pointer written to later */
  function(uint256) internal returns(uint256) a;

  constructor() public {
    a = foo;
    a(10);
  }
  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}

contract good7 {
  struct S {
    /* Uninitialized function pointer within a struct*/
    function(uint256) internal returns(uint256) a;
  }

  constructor() public {
    S memory s;
    s.a = foo;
    s.a(10);
  }

  function foo(uint256 i) internal returns(uint256) {
    return(i);
  }
}
