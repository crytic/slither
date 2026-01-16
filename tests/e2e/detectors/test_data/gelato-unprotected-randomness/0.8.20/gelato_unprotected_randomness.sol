// Mock GelatoVRFConsumerBase for what we need
abstract contract GelatoVRFConsumerBase {
    bool[] public requestPending;
    mapping(uint256 => bytes32) public requestedHash;

    function _fulfillRandomness(
        uint256 randomness,
        uint256 requestId,
        bytes memory extraData
    ) internal virtual;

    function _requestRandomness(
        bytes memory extraData
    ) internal returns (uint256 requestId) {
        requestId = uint256(requestPending.length);
        requestPending.push();
        requestPending[requestId] = true;

        bytes memory data = abi.encode(requestId, extraData);
        uint256 round = 111;

        bytes memory dataWithRound = abi.encode(round, data);
        bytes32 requestHash = keccak256(dataWithRound);

        requestedHash[requestId] = requestHash;
    }

}

contract C is GelatoVRFConsumerBase {
    address owner;
    mapping(address => bool) authorized;

    function _fulfillRandomness(
        uint256 randomness,
        uint256,
        bytes memory extraData
    ) internal override {
        // Do something with the random number
    }

    function bad() public {
        uint id = _requestRandomness(abi.encode(msg.sender));
    }

    function good() public {
        require(msg.sender == owner);
        uint id = _requestRandomness(abi.encode(msg.sender));
    }

    // This is currently a FP due to the limitation of function.is_protected
    function good2() public {
        require(authorized[msg.sender]);
        uint id = _requestRandomness(abi.encode(msg.sender));
    }

    function good3() public {
        if (msg.sender != owner) { revert(); }
        uint id = _requestRandomness(abi.encode(msg.sender));
    }

}
