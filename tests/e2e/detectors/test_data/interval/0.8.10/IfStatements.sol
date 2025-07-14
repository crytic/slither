// SPDX-License-Identifier: MIT
pragma solidity ^0.8.10;

contract SimpleIfTest {
    
    // Test 1: Most basic if-else
    function basicIf(uint256 x) public pure {
        if (x > 100) {
            // This branch should have: x ∈ [101, 255]
            x = 5;  // Just to have some operation
        } else {
            // This branch should have: x ∈ [0, 100]
            x = 6;  // Just to have some operation
        }
        // Final result: x ∈ [0, 255] but split into two domains
        // Domain 1: x ∈ [101, 255] 
        // Domain 2: x ∈ [0, 100]
    }
    
//     // Test 2: Simple assignment after if
//     function ifWithAssignment(uint256 x) public pure {
//         if (x > 100) {
//             // x should be constrained to [101, 255] here
//             x = 50;  // This should create a constraint violation warning
//         } else {
//             // x should be constrained to [0, 100] here  
//             x = 30;  // This is valid
//         }
//         // Expected: x ∈ {30, 50}
//         // But constraint check should show x=50 violates x > 100
//     }
    
//     // Test 3: Variable usage within constrained branch
//     function constrainedUsage(uint256 x) public pure {
//         uint256 result;
//         if (x > 100) {
//             // x ∈ [101, 255] in this branch
//             result = x - 50;  // result ∈ [51, 205]
//         } else {
//             // x ∈ [0, 100] in this branch
//             result = x + 10;  // result ∈ [10, 110]
//         }
//         // Expected: result ∈ [10, 110] ∪ [51, 205] = [10, 205]
//     }
}

// pragma solidity ^0.8.10;

// contract IfConditionalTests {
    
//     // Test 1: Simple if-else
//     function simpleIfElse(uint256 x) public pure returns (uint256) {
//         if (x > 100) {
//             x = 50;
//         } else {
//             x = 30;
//         }
//         // Expected: x ∈ {30, 50}
//         return x;
//     } // PASSED
    
//     // Test 2: If-else if-else chain
//     function ifElseIfElse(uint256 x) public pure returns (uint256) {
//         if (x > 100) {
//             x = 50;
//         } else if (x > 50) {
//             x = 25;
//         } else {
//             x = 10;
//         }
//         // Expected: x ∈ {10, 25, 50}
//         return x;
//     }
    
//     // Test 3: Long if-else if chain
//     function longIfElseChain(uint256 x) public pure returns (uint256) {
//         if (x > 200) {
//             x = 100;
//         } else if (x > 150) {
//             x = 75;
//         } else if (x > 100) {
//             x = 50;
//         } else if (x > 50) {
//             x = 25;
//         } else {
//             x = 10;
//         }
//         // Expected: x ∈ {10, 25, 50, 75, 100}
//         return x;
//     }
    
//     // Test 4: Nested if inside if-else
//     function nestedIf(uint256 x, uint256 y) public pure returns (uint256) {
//         uint256 result;
//         if (x > 100) {
//             if (y > 50) {
//                 result = 1;
//             } else {
//                 result = 2;
//             }
//         } else {
//             result = 3;
//         }
//         // Expected: result ∈ {1, 2, 3}
//         // Domain 1: x > 100 AND y > 50 → result = 1
//         // Domain 2: x > 100 AND y <= 50 → result = 2  
//         // Domain 3: x <= 100 → result = 3
//         return result;
//     } // FAILED
    
//     // // Test 5: If with revert
//     // function ifWithRevert(uint256 x) public pure returns (uint256) {
//     //     if (x > 100) {
//     //         revert("Too large");
//     //     } else {
//     //         x = 30;
//     //     }
//     //     // Expected: x ∈ {30} (x > 100 branch terminates)
//     //     return x;
//     // }
    
//     // // Test 6: Complex nested if-else if
//     // function complexNested(uint256 x, uint256 y) public pure returns (uint256) {
//     //     uint256 result;
//     //     if (x > 100) {
//     //         if (y > 80) {
//     //             result = 1;
//     //         } else if (y > 40) {
//     //             result = 2;
//     //         } else {
//     //             result = 3;
//     //         }
//     //     } else if (x > 50) {
//     //         if (y > 60) {
//     //             result = 4;
//     //         } else {
//     //             result = 5;
//     //         }
//     //     } else {
//     //         result = 6;
//     //     }
//     //     // Expected: result ∈ {1, 2, 3, 4, 5, 6}
//     //     // Multiple constraint combinations
//     //     return result;
//     // }
    
//     // // Test 7: If without else
//     // function ifWithoutElse(uint256 x) public pure returns (uint256) {
//     //     if (x > 100) {
//     //         x = 50;
//     //     }
//     //     // Expected: x ∈ [0, 50] ∪ [101, 255] → simplified to [0, 255] with {50} for x > 100
//     //     return x;
//     // }
    
//     // // Test 8: Sequential independent ifs
//     // function sequentialIfs(uint256 x) public pure returns (uint256) {
//     //     if (x > 100) {
//     //         x = 50;
//     //     } else {
//     //         x = 25;
//     //     }
        
//     //     if (x > 40) {
//     //         x = 10;
//     //     } else {
//     //         x = 5;
//     //     }
//     //     // Expected: x ∈ {5, 10}
//     //     // First if: x ∈ {25, 50}
//     //     // Second if: 50 > 40 → x = 10, 25 ≤ 40 → x = 5
//     //     return x;
//     // }
    
//     // // Test 9: If with require
//     // function ifWithRequire(uint256 x) public pure returns (uint256) {
//     //     if (x > 100) {
//     //         require(x < 200, "Out of range");
//     //         x = 50;
//     //     } else {
//     //         x = 30;
//     //     }
//     //     // Expected: x ∈ {30, 50}
//     //     // x > 100 branch has additional constraint x < 200
//     //     return x;
//     // }
    
//     // // Test 10: Multiple conditions in if
//     // function multipleConditions(uint256 x, uint256 y) public pure returns (uint256) {
//     //     if (x > 100 && y > 50) {
//     //         return 1;
//     //     } else if (x > 100) {
//     //         return 2;
//     //     } else {
//     //         return 3;
//     //     }
//     //     // Expected: return ∈ {1, 2, 3}
//     //     // Domain 1: x > 100 AND y > 50 → return = 1
//     //     // Domain 2: x > 100 AND y <= 50 → return = 2
//     //     // Domain 3: x <= 100 → return = 3
//     // }
    
//     // // Test 11: If with range result
//     // function ifWithRange(uint256 x) public pure returns (uint256) {
//     //     if (x > 100) {
//     //         x = x - 50;  // x was > 100, now x ∈ [51, 205] (assuming uint8 max 255)
//     //     } else if (x > 50) {
//     //         x = x + 10;  // x was ∈ [51, 100], now x ∈ [61, 110]
//     //     } else {
//     //         x = x * 2;   // x was ∈ [0, 50], now x ∈ [0, 100]
//     //     }
//     //     // Expected: x ∈ [0, 100] ∪ [51, 205] = [0, 205]
//     //     // More precisely: x ∈ [0, 100] ∪ [61, 110] ∪ [51, 205]
//     //     // Which simplifies to: x ∈ [0, 205]
//     //     return x;
//     // }
    
//     // // Test 12: Range with constraints
//     // function rangeWithConstraints(uint256 x) public pure returns (uint256) {
//     //     if (x > 200) {
//     //         x = x / 2;   // x was > 200, now x ∈ [101, 127] (assuming uint8 max 255)
//     //     } else if (x > 100) {
//     //         x = x - 20;  // x was ∈ [101, 200], now x ∈ [81, 180]
//     //     } else {
//     //         // x unchanged, x ∈ [0, 100]
//     //     }
//     //     // Expected: x ∈ [0, 100] ∪ [81, 180] ∪ [101, 127]
//     //     // Which simplifies to: x ∈ [0, 180]
//     //     return x;
//     // }
// }