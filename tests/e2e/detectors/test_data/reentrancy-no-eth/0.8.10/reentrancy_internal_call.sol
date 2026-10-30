contract ReentrancyInternalCall {
    uint256 counter;
    uint256 other;

    // Should be detected: counter is read, then _callThenWrite calls out and writes it
    function bad() external {
        require(counter != 9);
        _callThenWrite();
    }

    // Should be detected: the read happens in the argument of the internal call
    function badArgument() external {
        _callThenWriteValue(counter);
    }

    // Should be detected: the call and the write are two internal calls deep
    function badNested() external {
        require(counter != 1);
        _nested();
    }

    // Should not be detected: the callee writes before its external call
    function goodWriteBeforeCall() external {
        require(other != 9);
        _writeThenCall();
    }

    // Should not be detected: nothing is read before the internal call
    function goodNoRead() external {
        _callThenWriteOther();
    }

    function _callThenWrite() internal {
        (bool success, ) = msg.sender.call("");
        require(success);
        counter = 9;
    }

    function _callThenWriteValue(uint256 value) internal {
        (bool success, ) = msg.sender.call("");
        require(success);
        counter = value + 1;
    }

    function _nested() internal {
        _callThenWrite();
    }

    function _writeThenCall() internal {
        other = 9;
        (bool success, ) = msg.sender.call("");
        require(success);
    }

    function _callThenWriteOther() internal {
        (bool success, ) = msg.sender.call("");
        require(success);
        other = 1;
    }
}
