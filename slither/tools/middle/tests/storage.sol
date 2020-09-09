pragma solidity >=0.4.16 <0.7.0;

contract SimpleStorage {
    uint storedData;

    function a() public {
        uint x = storedData;
        b();
        uint z = storedData;
    }

    function b() public {
        storedData = storedData + 1;
    }
}