pragma solidity ^0.4.24;

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
