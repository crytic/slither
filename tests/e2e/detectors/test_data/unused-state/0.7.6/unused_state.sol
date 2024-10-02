//pragma solidity ^0.4.24;

contract A{
    address unused;
    address unused2;
    address unused3;
    address unused4;
    address used;
}

contract B is A{

    fallback () external{
        used = address(0);
    }
}

library C {
    uint internal constant good = 0x00; // other contract can access this constant
    function c() public pure returns (uint){
        return 0;
    }
    
}

abstract contract F {
    uint private bad1 = 0x00;
    uint private good1 = 0x00;
    uint internal good2 = 0x00;
    function use() external returns (uint){
        return good1;
    }
}

abstract contract H {
    uint private good1 = 0x00;
    uint internal good2 = 0x00;
    uint internal bad1 = 0x00;
}

contract I is H {
    function use2() external returns (uint){
        return good2;
    }
}