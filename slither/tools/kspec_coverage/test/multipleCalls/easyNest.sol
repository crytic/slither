pragma solidity >=0.4.24;

contract Callee {
  uint temperature = 0;
  function tempDelta(uint x) public {
    temperature = add(temperature, x);
  }

  function add(uint x, uint y) internal pure returns (uint z) {
    z = x + y;
    require(z >= x);
  }
}

contract easyNest {
  Callee callee;
  function raiseTemp(uint x) public {
    callee.tempDelta(x);
  }
}
