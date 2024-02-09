library Lib {
  function f(Hello h) external {

  }
}
contract Hello {
    using Lib for Hello;

    function test() external {
      this.f();
    }
}

