// SPDX-License-Identifier: GPL3
pragma solidity ^0.8.0;

import "./IERC20.sol";

contract A {
  IERC20 private token;

  function foo() view internal {
    token.balanceOf(address(this));
  }

  function encodeData(uint256 number, string memory text) public pure returns (bytes memory) {
      return abi.encode(number, text);
  }
}

contract B is A {
  function bar() view public {
     foo();
  }
}


contract C {
    B public b;
    function pop() view public {
        b.bar();
    }
}