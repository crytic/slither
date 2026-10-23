contract ViewPureStrictEquality {
    uint256 public immutable deployBlock;
    uint256 public deadline;
    uint256 public releases;

    constructor(uint256 deadline_) {
        deployBlock = block.number;
        deadline = deadline_;
    }

    function isDeployBlockExternal() external view returns (bool) {
        return block.number == deployBlock;
    }

    function isDeployBlockPublic() public view returns (bool) {
        return block.number == deployBlock;
    }

    function isZeroPure(uint256 value) public pure returns (bool) {
        return value == 0;
    }

    function _isDeadline() internal view returns (bool) {
        return block.timestamp == deadline;
    }

    function releaseIfDeadline() external {
        if (_isDeadline()) {
            releases += 1;
        }
    }
}
