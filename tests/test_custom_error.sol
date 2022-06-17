contract A {
    error E(A a);

    function f() payable external {
      g();
    }
    
    function g() private {
      bool something = h();
      if (something) {
        revert E(this);
      }
    }

    function h() private returns (bool something) {
    }
}


interface I {
  enum Enum { ONE, TWO, THREE }
  error SomethingSomething(Enum e);
}

abstract contract A2 is I {
}

contract B is A2 {
  
  function f() external {
    revert SomethingSomething(Enum.ONE);
  }
}

