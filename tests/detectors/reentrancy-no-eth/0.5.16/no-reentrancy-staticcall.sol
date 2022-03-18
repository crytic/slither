library MyLibrary {

  function aViewCall(address token) internal view {
    (bool success ,) = token.staticcall(abi.encodeWithSignature("decimals"));
    require(success, "call failed");
  }
}

contract A {
  uint256 private protectMe = 1;
  function good() external {
    MyLibrary.aViewCall(0x6B175474E89094C44Da98b954EedeAC495271d0F);
    protectMe += 1;
  }
  function good1() external {
    (bool success,) = address(MyLibrary).staticcall(abi.encodeWithSignature("aViewCall(address)"));
    require(success, "call failed");
    protectMe += 1;
  }
}
