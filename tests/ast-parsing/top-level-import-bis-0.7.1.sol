import "./helper/helper.sol" as Helper;

contract C {
  function f() external {
    Helper._require(msg.sender != address(0), 42);
  }
}
