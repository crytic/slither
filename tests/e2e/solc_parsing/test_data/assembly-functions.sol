contract A {
    function foo() public {
        assembly {
            function f() { function z() { function x() { g() } x() } z() }
            function w() { function a() {} function b() { a() } b() }
            function g() {
                f()
            }
            g()
        }
    }
}

// Issue https://github.com/crytic/slither/issues/2655
contract B {
  function test(int256 a) internal {
    assembly  {
      function a() {}
      function b() { a() }
    }
  }
}