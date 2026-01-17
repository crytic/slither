pragma solidity ^0.8.0;

contract C {

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