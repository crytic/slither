pragma solidity >=0.4.25 <0.9.0;

contract TxOriginModifiers {
    address owner;

    modifier originRequire() {
        require(tx.origin == owner);
        _;
    }

    modifier originIf() {
        if (tx.origin != owner) {
            revert();
        }
        _;
    }

    modifier originAssert() {
        assert(tx.origin == owner);
        _;
    }

    modifier senderOnly() {
        require(msg.sender == owner);
        _;
    }

    modifier senderIsOrigin() {
        require(msg.sender == tx.origin);
        _;
    }

    modifier readOrigin() {
        address origin = tx.origin;
        _;
    }

    function guardedRequire() public originRequire {}
    function guardedIf() public originIf {}
    function guardedAssert() public originAssert {}
    function guardedSender() public senderOnly {}
    function guardedSenderIsOrigin() public senderIsOrigin {}
    function nonConditionalOrigin() public readOrigin {}
}

contract InheritedTxOriginModifiers is TxOriginModifiers {
    function inheritedGuard() public originRequire {}
}
