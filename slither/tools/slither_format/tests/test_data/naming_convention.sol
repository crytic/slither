pragma solidity ^0.4.24;

contract naming {

    enum Numbers {ONE, TWO}
    enum numbers {ONE, TWO}

    numbers nums = numbers.TWO;
   
    uint constant MY_CONSTANT = 1;
    uint constant MY_other_CONSTANT = 2;

    uint Var_One = 1; uint varTwo = 2;

    struct test {
        uint a;
    }

    struct Test {
        uint a;
    }

    test t;
    
    event Event_(uint);
    event event_(uint);

    uint Number2;
    
    function getOne(bytes32 b) view public returns(uint) {
      return MY_other_CONSTANT;
    }
    
    function getOne(uint i) view public returns(numbers) {
      numbers num;
      num = numbers.ONE;
      return(num);      
    }
    
    function getOne() view public returns(uint) 
    {
      uint naming;
      naming = GetOne(naming);
      event_(naming);
      return 1;
    }

    function GetOne(uint i) view public returns (uint) 
    {
      return (1 + Number2);
    }

    function setInt(uint number1, uint Number2) public
    {
      uint i = number1 + Number2;
    }


    modifier CantDo() {
        _;
    }

    modifier canDo() {
        _;
    }
}

contract Test {
  naming n;

  function foo() {
    n.GetOne(10);
  }
}

contract T {
    uint private _myPrivateVar;
    uint _myPublicVar;

    modifier ModifierTest() {
      _;
    }
    
    modifier modifierTestContractTypes(naming m1) {
      naming m2;
      _;
    }
    
    function functionTestModifier(uint i) public ModifierTest returns(uint) {
      return _myPrivateVar;
    }
    
    function functionTestContractTypes(naming n1) public returns(naming) {
      naming n2;
      return(n2);
    }
    
    function test(uint _unused, uint _used) public returns(uint){
      return _used;
    }


    uint k = 1;

    uint constant M = 1;

    uint l = 1;
}
