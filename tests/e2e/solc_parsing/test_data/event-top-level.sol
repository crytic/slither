event MyEvent(uint256 a);

uint256 constant A = 3;
event MyEvent2(uint8[A]);

contract T {
  type MyType is uint256;
  event MyCustomEvent(MyType mytype);

  function a() public {
    emit MyEvent(2);
  }

  function b() public {
    emit MyEvent2([1,2,3]);
  }
}
