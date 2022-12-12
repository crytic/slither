contract C { 

    function f() internal returns (uint a) { 
        assembly { 
            a := shr(a, 8) 
        } 
    } 
} 