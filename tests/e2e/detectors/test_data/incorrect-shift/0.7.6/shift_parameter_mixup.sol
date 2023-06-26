contract C { 

    function f() internal returns (uint a, uint b) { 
        assembly { 
            a := shr(a, 8) 
            b := shl(248, 0xff)
        } 
    } 
} 