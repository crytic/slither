// This tests for redundant top-level expressions in statements.

contract RedundantStatementsContract {

    constructor() public {
        uint;
        bool;
        RedundantStatementsContract;
    }

    function test() public returns (uint) {
        uint;
        assert;
        test;
        return 777;
    }
}