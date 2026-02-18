pragma solidity 0.8.28;

contract TransientDeleteBad {
    address transient _lock;

    // Bad: delete on transient variable
    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        delete _lock;
    }
}

contract TransientDeleteGood {
    address transient _lock;

    // Good: explicit zero assignment instead of delete
    function guarded() external {
        require(_lock == address(0), "locked");
        _lock = msg.sender;
        _lock = address(0);
    }
}
