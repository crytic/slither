contract C1 {
    // non-payable constructor
    constructor() public {}

    // non-payable fallback
    function() external {}
}

contract C2 {
    // payable constructor
    constructor() public payable {}

    // payable fallback
    function() external payable {}
}

contract C3 {
    // internal constructor
    constructor() internal {}

    modifier modifierNoArgs() { _; }
    modifier modifierWithArgs(uint a) { _; }

    function f() public modifierNoArgs modifierWithArgs(block.timestamp) {}
}

contract C4 {
    function hasArgs(uint, uint) public {}
    function hasReturns() public returns (uint) {}
    function hasArgsAndReturns(uint a, uint b) public returns (uint c) {}
}

contract C5 {
    function payableFunc() public payable {}
    function externalFunc() external {}
    function publicFunc() public {}
    function internalFunc() internal {}
    function privateFunc() private {}
    function pureFunc() public pure {}
    function viewFunc() public view {}
    function abstractFunc() public;
}