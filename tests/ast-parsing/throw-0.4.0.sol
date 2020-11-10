contract C {
    function f() public {
        if (msg.sender.balance == 0) {
            throw;
        }
    }
}