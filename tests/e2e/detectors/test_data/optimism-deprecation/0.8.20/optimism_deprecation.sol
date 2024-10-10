interface GasPriceOracle {
    function scalar() external view returns (uint256);
    function baseFee() external view returns (uint256);
}

interface L1BlockNumber {
    function q() external view returns (uint256);
}

contract Test {
    GasPriceOracle constant OPT_GAS = GasPriceOracle(0x420000000000000000000000000000000000000F);
    L1BlockNumber constant L1_BLOCK_NUMBER = L1BlockNumber(0x4200000000000000000000000000000000000013);

    function bad() public {
        OPT_GAS.scalar();    
    }

    function bad2() public {
        L1_BLOCK_NUMBER.q();    
    }

    function good() public {
        OPT_GAS.baseFee();    
    }


}
