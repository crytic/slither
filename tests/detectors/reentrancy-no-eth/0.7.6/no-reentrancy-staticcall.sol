interface IERC20 {
    function decimals() external view returns (uint8);
}

library MyLibrary {

  function aViewCall(address token) internal view {
    (bool success ,  ) = token.staticcall(
            abi.encodeWithSelector(IERC20.decimals.selector)
            );
     require(success, "call failed");
  }
}

contract A {
  uint256 private protectMe = 1;
  function foo() external {
    MyLibrary.aViewCall(0x6B175474E89094C44Da98b954EedeAC495271d0F);
    protectMe += 1;
  }
}
