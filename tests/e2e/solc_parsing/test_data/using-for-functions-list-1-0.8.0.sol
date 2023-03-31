
struct Data { mapping(uint => bool) flags; }

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

    using {L1.a, L1.b} for Data;
    Data knownValues;

    function libCall(uint value) public {
        require(knownValues.a(value));
    }

}
