contract C {
    function f(bytes calldata paramA) external returns (uint256 retA) {
        assembly {
            retA := paramA.offset
            retA := add(retA, batchData.length)
        }
    }

}
