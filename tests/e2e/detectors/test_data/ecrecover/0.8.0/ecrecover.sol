contract A {
    struct Info {
        uint tokenId;
        address owner;
        // uint nonce
    }
    uint maxBreed = 5;
    mapping(uint => mapping(uint => address)) list;
    mapping(uint => uint) count;
    mapping(address => uint256) nonces;

    function mint(uint tokenId, address addr) internal {
        require(count[tokenId] < maxBreed, "");
        list[tokenId][count[tokenId]] = addr;
        count[tokenId]++;
    }

    function bad_noSignerCheck_noNonce(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );
        address receiver = ecrecover(data, v, r, s);
        mint(info.tokenId, receiver);
    }

    function bad_noSignerCheck_withNonce(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info, nonces[msg.sender]++));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );
        address receiver = ecrecover(data, v, r, s);
        mint(info.tokenId, receiver);
    }

    function bad_withRequire_noNonce(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );
        address receiver = ecrecover(data, v, r, s);
        require(receiver != address(0), "ECDSA: invalid signature");
        mint(info.tokenId, receiver);
    }

    function bad_withIF_noNonce(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 hash = keccak256(abi.encode(info));
        bytes32 data = keccak256(
            abi.encodePacked("\x19Ethereum Signed Message:\n32", hash)
        );
        address receiver = ecrecover(data, v, r, s);
        if (receiver == address(0)) revert();
        mint(info.tokenId, receiver);
    }

    function good_withNonceAndSignerCheck(
        Info calldata info,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 data = keccak256(
            abi.encodePacked(
                "\x19Ethereum Signed Message:\n32",
                keccak256(abi.encode(info, nonces[msg.sender]++))
            )
        );
        address receiver = ecrecover(data, v, r, s);
        require(receiver != address(0), "ECDSA: invalid signature");
        mint(info.tokenId, receiver);
    }
}
