contract YYY {
    mapping(address => uint256) private _counters;
    function _getPackedBucketGlobalState(uint256 bucketId) internal view returns (uint256 packedGlobalState) {
        assembly {
            mstore(0x0, bucketId)
            mstore(0x20, _counters.slot)
            let slot := keccak256(0x0, 0x40)
            packedGlobalState := sload(slot)
        }
    }
}


contract XXX is YYY {
    function getPackedBucketGlobalState(uint256 bucketId) external {
        _getPackedBucketGlobalState(bucketId);
    }
}