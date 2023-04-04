interface BaseInterface {
    function f1() external returns(uint);
    function f2() external returns(uint);
}

interface BaseInterface2 {
    function f3() external returns(uint);
}

abstract contract DerivedContract_bad0 is BaseInterface, BaseInterface2 {
    function f1() external override returns(uint){
        return 42;
    }
}

abstract contract AbstractContract_bad1 {
    function f1() external virtual returns(uint);
    function f2() external returns(uint){
        return 42;
    }
}

abstract contract BaseInterface3 {
    function get(uint) external virtual returns(uint);
}

abstract contract DerivedContract_bad2 is BaseInterface3 {
  // the mapping type get(uint => bool) does NOT match the function get(uint) => uint
  // mapping(uint => bool) public override get; <-- disallowed by solidity compiler: Overriding public state variable return types differ.
  function f1() external returns(uint){
    return 42;
  }
}

contract DerivedContract_good is BaseInterface3 {
  // In solc >= 0.5.1, the mapping type get(uint => uint) matches the function get(uint) => uint
  mapping(uint => uint) public override get;
  function f1() external returns(uint){
    return 42;
  }
}
