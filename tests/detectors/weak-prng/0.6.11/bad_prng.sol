contract BadPRNG{
    event Time(uint);

    function bad0() external{
      uint i = block.timestamp % 10;
    }   

    function bad1() external{
      uint i = now % 10;
    }

    function bad2() external{
      uint i = uint256(blockhash(10000)) % 10;
    }
    
    function foo() public returns (uint) {
      return(uint256(blockhash(10000)));
    }

    function bad3() external{
      uint i = foo() % 10;
    }   

    function good() external{
        emit Time(block.timestamp);
    }
}

