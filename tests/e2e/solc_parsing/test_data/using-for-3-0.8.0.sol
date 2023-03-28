using {a} for Data;

struct Data { mapping(uint => bool) flags; }

function a(Data storage self, uint value, uint value2) returns(bool){
    return false;
}

library Lib {
    function a(Data storage self, uint value) public
        view
        returns (bool)
    {
        return true;
    }

}

contract C {
    using Lib for Data;
    Data knownValues;

    function libCall(uint value) public {
        require(knownValues.a(value));
    }

}