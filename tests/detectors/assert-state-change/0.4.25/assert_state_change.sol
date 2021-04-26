contract A {

  uint s_a;

  /* Direct state change in assert is NOT ok */
  function bad0() public {
    assert((s_a += 1) > 10);
  }

  /* Direct state change in assert is NOT ok */
  function bad1(uint256 a) public {
    assert((s_a += a) > 10);
  }

  /* State change via functions calls in assert is NOT ok */
  function bad2_callee() public returns (bool) {
    return (s_a += 1) > 10;
  }
  function bad2() public {
    assert(bad2_callee());
  }


  /* Parameter use is ok */
  function good0(uint256 a) public {
    assert(a > 10);
  }

  /* Parameter change is ok */
  function good1(uint256 a) public {
    assert((a += 1) > 10);
  }

  /* State change in require is ok */
  function good2(uint256 a) public {
    require(a == (s_a += 1));
  }
  
}
