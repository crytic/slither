pragma experimental ABIEncoderV2;

interface I {}

contract C {
    I[6] interfaceArray;

    function test_decode(bytes memory data) public {
        interfaceArray = abi.decode(data, (I[6]));
    }
}