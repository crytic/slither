pragma solidity ^0.4.0;

contract C {

    modifier needsPayment() {
        require(msg.value > 0);
        _;
    }
    
    // DETECT: Direct msg.value in non-payable
    function test1() external {
        if (msg.value > 0) { } // Issue
    }
    
    // DETECT: msg.value in view function
    function test2() external view returns (uint) {
        return msg.value; // Always 0
    }
    
    // DETECT: Modifier with msg.value on non-payable
    function test3() external needsPayment {
        // Can never execute
    }
    
    // OK: Payable function
    function test4() external payable {
        require(msg.value > 0); // Valid
    }
    
    // OK: Internal called from payable
    function test5Internal() internal {
        require(msg.value > 0); // OK if called from payable
    }
    
    function test5() external payable {
        test5Internal(); // Valid call chain
    }
    
    // DETECT: Complex call chain, no payable entry
    function helper() internal view returns (bool) {
        return msg.value > 0;
    }
    
    function middle() internal view returns (bool) {
        return helper();
    }
    
    function entry() external view returns (bool) {
        return middle(); // Detects msg.value in helper
    }
}