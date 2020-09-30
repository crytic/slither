contract C1 {
    // non-payable constructor
    function C1() public {}

    // non-payable fallback
    function() public {}
}

contract C2 {
    // payable constructor
    function C2() public payable {}

    // payable fallback
    function() public payable {}
}

contract C3 {
    // internal constructor
    function C3() internal {}

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