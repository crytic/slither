pragma solidity 0.7.6;

interface IERC20 {
    function transferFrom(address, address, uint256) external returns (bool);
}

contract Settlement {
    IERC20 token;
    address owner;

    function good_ecrecover_in_require(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encodePacked(from, to, amount));
        require(ecrecover(digest, v, r, s) == from, "bad signature");
        token.transferFrom(from, to, amount);
    }

    function good_ecrecover_in_local(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encodePacked(from, to, amount));
        address signer = ecrecover(digest, v, r, s);
        if (signer != from) {
            revert("bad signature");
        }
        token.transferFrom(from, to, amount);
    }

    function bad_no_signature(address from, address to, uint256 amount) external {
        token.transferFrom(from, to, amount);
    }

    function bad_ecrecover_compared_to_other_address(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encodePacked(from, to, amount));
        require(ecrecover(digest, v, r, s) == owner, "bad signature");
        token.transferFrom(from, to, amount);
    }

    function bad_ecrecover_result_ignored(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encodePacked(from, to, amount));
        address signer = ecrecover(digest, v, r, s);
        signer;
        token.transferFrom(from, to, amount);
    }

    function bad_digest_chosen_by_caller(
        address from,
        address to,
        uint256 amount,
        bytes32 digest,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        require(ecrecover(digest, v, r, s) == from, "bad signature");
        token.transferFrom(from, to, amount);
    }
}
