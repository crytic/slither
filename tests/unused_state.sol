//pragma solidity ^0.4.24;

contract A{
    address unused;
    address unused2;
    address unused3;
    address unused4;
    address used;
}

contract B is A{

    function () external{
        used = address(0);
    }
}
