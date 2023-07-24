interface I {}
enum A {a,b}

contract C {
    I[6] interfaceArray;
    A[6] enumArray;

    function test_decode_interface_array(bytes memory data) public {
        interfaceArray = abi.decode(data, (I[6]));
    }

    function test_decode_enum_array(bytes memory data) public {
        enumArray = abi.decode(data, (A[6]));
    }

}
