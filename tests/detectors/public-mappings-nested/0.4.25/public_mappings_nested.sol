// This is used to test detection of public mappings with nested variables. This was an issue in Solidity 0.4.x.
pragma solidity ^0.4.0;

contract Bug {

    struct innerStruct {
        uint x;
    }

    struct outerStruct {
        innerStruct inner;
    }

    mapping(uint => outerStruct) public testMapping;
    mapping(uint => uint) public testMapping2;
    mapping(uint => address) public testMapping3;

    constructor() public {
        testMapping[0].inner.x = 42;
    }
}

contract Test{

    function f() public returns(uint){
        Bug b = new Bug();
        return b.testMapping(0).x;
    }
}