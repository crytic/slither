
struct Data { mapping(uint => bool) flags; }

function d(Data storage self, uint value) returns(bool){
    return true;
}

library L1 {
    function a(Data storage self, uint value) public
        view
        returns (bool)
    {
        return true;
    }

    function b(Data storage self, uint value) public
        view
        returns (bool)
    {
        return true;
    }

    function c(Data storage self, uint value) public
        view
        returns (bool)
    {
        return true;
    }

}

contract C {

    using {L1.a, L1.b, d} for Data;
    Data knownValues;

    function topLevelCall(uint value) public {
        require(knownValues.d(value));
    }

}
