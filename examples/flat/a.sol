pragma solidity 0.8.19;

error RevertIt();

contract Example {
  function reverts() external pure {
    revert RevertIt();
  }
}