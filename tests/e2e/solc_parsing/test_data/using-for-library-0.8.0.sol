
struct Data { mapping(uint => bool) flags; }
using L1 for Data global;
using {d} for Data global;

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
