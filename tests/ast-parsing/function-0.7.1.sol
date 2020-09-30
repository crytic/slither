contract C1 {
    // non-payable constructor
    constructor() {}

    fallback() external {}

    receive() external payable {}
}

contract C2 {
    // payable constructor
    constructor() payable {}

    fallback() external {}

    receive() external payable {}
}

abstract contract C3 {
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

abstract contract C5 {
    function payableFunc() public payable {}
    function externalFunc() external {}
    function publicFunc() public {}
    function internalFunc() internal {}
    function privateFunc() private {}
    function pureFunc() public pure {}
    function viewFunc() public view {}
    function abstractFunc() public virtual;
}

abstract contract C6 {
    function abstractFunc() public virtual;
    function abstractFunc2() public virtual;
}

abstract contract C7 {
    function abstractFunc3() public virtual;
}

contract C8 is C5, C6, C7 {
    function abstractFunc() public virtual override(C5, C6) {}
    function abstractFunc2() public virtual override(C6) {}
    function abstractFunc3() public virtual override {}
}

function freeFunc() {}