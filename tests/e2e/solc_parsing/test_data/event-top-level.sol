event MyEvent(uint256 a);

contract T {
  function a() public {
    emit MyEvent(2);
  }
}
