contract A {
    struct Info {
        uint tokenId;
        address owner;
        // uint nonce
    }
    uint maxBreed = 5;
    mapping (uint => mapping(uint => address)) list;
    mapping (uint => uint) count;
    function mint(uint tokenId, address addr) internal {
        require(count[tokenId] < maxBreed, "");
        list[tokenId][count[tokenId]] = addr;
        count[tokenId]++;
    }
    function verify(Info calldata info, uint8 v, bytes32 r, bytes32 s) external {
        bytes32 hash = keccak256(abi.encode(info));
        bytes32 data =
            keccak256(
                abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
            );
        address receiver = ecrecover(data, v, r, s);
        // require(signer != address(0), "ECDSA: invalid signature");
        mint(info.tokenId, receiver);
    }
}