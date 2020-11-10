pragma solidity ^0.4.25;

contract BaseContract {
    uint blockhash;
    uint now;

    event revert(bool condition);
}

contract ExtendedContract is BaseContract {
    uint ecrecover = 7;

    function assert(bool condition) public {
        uint msg;
    }
}

contract FurtherExtendedContract is ExtendedContract {
    uint blockhash = 7;
    uint this = 5;
    uint abi;

    modifier require {
        assert(msg.sender != address(0));
        uint keccak256;
        uint sha3;
        _;
    }
}

contract Reserved{
    address mutable;

}
