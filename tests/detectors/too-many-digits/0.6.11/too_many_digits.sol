// pragma solidity ^0.5.1;

contract C {
    uint balance;
    
    /**
     * @dev Variables are not Ok - using too many digits in place of the Ether denomination.
     */
    function f() external {
        uint x1 = 0x000001;
        uint x2 = 0x0000000000001;
        uint x3 = 1000000000000000000;
        uint x4 = 100000;
        balance += x1 + x2 + x3 + x4;
    }
    
    /**
     * @dev Variables are Ok - not using too many digits.
     */
    function h() external {
        uint x1 = 1000;
        uint x2 = 100000;
        balance += x1 + x2 + 100;
    }
    
    /**
     * @dev Variables are Ok - Using Ether denominations.
     */
    function i() external {
        uint x1 = 1 wei + 10 wei + 100 wei + 1000 wei + 10000 wei;
        uint x2 = 1 szabo + 10 szabo + 100 szabo + 1000 szabo + 10000 szabo;
        balance += x1 + x2;
    }

    function good() external{

        uint x = 1 ether;
    }

    function good2() external {
        address x = 0x00000000000C2E074eC69A0dFb2997BA6C7d2e1e;
    }
    
}
