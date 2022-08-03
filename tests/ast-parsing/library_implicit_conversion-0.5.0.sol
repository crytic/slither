library LibByte{
    function t(uint, bytes1) internal returns(uint){
        return 0x1;
    }
    function t(uint, bytes32) internal returns(uint){
        return 0x32;
    }

}


contract TestByte{
    using LibByte for uint;
    function test() public returns(uint){
        uint a;
        return a.t(0x10); // for byte, this will match only bytes1
    }
}

library LibUint{
    function t(uint, uint8) internal returns(uint){
        return 0x1;
    }
    function t(uint, uint256) internal returns(uint){
        return 0x32;
    }

}

contract TestUint{

    using LibUint for uint;
    function test() public returns(uint){
        uint a;
        return a.t(2**8); // above uint8
    }
}

library LibInt{
    function t(uint, int8) internal returns(uint){
        return 0x1;
    }
    function t(uint, int256) internal returns(uint){
        return 0x32;
    }

}

contract TestUintWithVariableiAndConversion{

    using LibInt for uint;
    function test() public returns(uint){
        uint a;
        int16 v;
        return a.t(v); // above uint8
    }
}
