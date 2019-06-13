contract Test {
  function foo() public returns (uint) {
    uint i;
    return(i+10);
  }

  function foobar(uint i) public returns (uint) {
    return(i+10);
  }
}
