contract UsingEcrecover {
    function bad() public {
        address signer = ecrecover(
            bytes32(0),
            uint8(1),
            bytes32(0),
            bytes32(0)
        );
    }
}
