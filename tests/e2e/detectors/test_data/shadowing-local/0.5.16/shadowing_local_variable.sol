// pragma solidity ^0.4.24;

contract BaseContract {
    uint x = 5;
    uint y = 5;
}

contract ExtendedContract is BaseContract {
    uint x = 7;

    function z() public pure {}

    event v();
}

contract FurtherExtendedContract is ExtendedContract {
    uint x = 7;


    modifier w {
        assert(msg.sender != address(0));
        _;
    }

    function shadowingParent(uint x) public pure { int y; uint z; uint w; uint v; }
}

contract LocalReturnVariables {
    uint state;
    function shadowedState() external view returns(uint state) {
        return state;
    } 
    function shadowedReturn() external view returns(uint local) {
        uint local = 1;
        return local;
    } 
    function good() external view returns(uint val1) {
        return val1;
    }
}