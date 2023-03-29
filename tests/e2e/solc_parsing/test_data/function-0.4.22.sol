contract C1 {
    // non-payable constructor
    function C1() public {}

    // non-payable fallback
    function() public {}
}

contract C1A {
    constructor() public {}
}

contract C1B {
    function C1B() public {}
    constructor() public {}
}

contract C2 {
    // payable constructor
    function C2() public payable {}

    // payable fallback
    function() public payable {}
}

contract C2A {
    constructor() public payable {}
}

contract C2B {
    function C2B() public payable {}
    constructor() public payable {}
}

contract C3 {
    // internal constructor
    constructor() internal {}

    modifier modifierNoArgs() { _; }
    modifier modifierWithArgs(uint a) { _; }

    function f() public modifierNoArgs modifierWithArgs(block.timestamp) {}
}

contract C4 {
    function hasArgs(uint, uint) {}
    function hasReturns() public returns (uint) {}
    function hasArgsAndReturns(uint a, uint b) public returns (uint c) {}
}

contract C5 {
    function constantFunc() constant {}
    function payableFunc() payable {}
    function externalFunc() external {}
    function publicFunc() public {}
    function internalFunc() internal {}
    function privateFunc() private {}
    function pureFunc() pure {}
    function viewFunc() view {}
    function abstractFunc();
}