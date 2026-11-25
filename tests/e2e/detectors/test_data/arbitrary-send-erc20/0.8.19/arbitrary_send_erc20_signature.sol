pragma solidity 0.8.19;

interface IERC20 {
    function transferFrom(address, address, uint256) external returns (bool);
}

interface IERC1271 {
    function isValidSignature(bytes32 hash, bytes calldata signature) external view returns (bytes4);
}

library SafeTransferLib {
    function safeTransferFrom(address token, address from, address to, uint256 amount) internal {}
}

library SignatureCheckerLib {
    function isValidSignatureNowCalldata(address signer, bytes32 hash, bytes calldata signature)
        internal
        view
        returns (bool)
    {
        return signer != address(0) && hash != bytes32(0) && signature.length != 0;
    }
}

library SignatureChecker {
    function isValidSignatureNow(address signer, bytes32 hash, bytes memory signature)
        internal
        view
        returns (bool)
    {
        return signer != address(0) && hash != bytes32(0) && signature.length != 0;
    }
}

library ECDSA {
    function recover(bytes32 hash, bytes memory signature) internal pure returns (address) {
        return hash == bytes32(0) || signature.length == 0 ? address(0) : address(1);
    }
}

library FundingLib {
    function wrap(address account) internal pure returns (address) {
        return account;
    }
}

error InvalidSignature();

struct Offer {
    address maker;
    address taker;
    uint256 amount;
    uint256 nonce;
}

struct Order {
    address maker;
    address taker;
    uint256 amount;
    uint256 id;
    bytes32 hash;
    bytes payload;
}

abstract contract OfferReceiver {
    using SignatureCheckerLib for address;

    function _hash(Offer calldata offer) internal pure returns (bytes32) {
        return keccak256(abi.encode(offer));
    }

    function _validateOffer(Offer calldata offer, bytes calldata signature) internal view {
        if (!offer.maker.isValidSignatureNowCalldata(_hash(offer), signature)) {
            revert InvalidSignature();
        }
    }

    function _validateTaker(Offer calldata offer, bytes calldata signature) internal view {
        if (!offer.taker.isValidSignatureNowCalldata(_hash(offer), signature)) {
            revert InvalidSignature();
        }
    }

    function _validateOfferVia(Offer calldata offer, bytes calldata signature) internal view {
        _validateOffer(offer, signature);
    }

    function _isOfferValid(Offer calldata offer, bytes calldata signature)
        internal
        view
        returns (bool)
    {
        _validateOffer(offer, signature);
        return true;
    }
}

abstract contract Funding {
    using FundingLib for address;

    address internal token;
    mapping(address => bool) internal approved;
    mapping(uint256 => bytes32) internal digests;
    uint256 internal failures;
}

contract Settlement is Funding, OfferReceiver {
    using SafeTransferLib for address;

    bytes32 internal constant DOMAIN = keccak256("domain");
    bytes32 internal constant TRANSFER_TYPEHASH =
        keccak256("Transfer(address from,address to,uint256 amount)");

    function _typed(bytes32 structHash) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(hex"1901", DOMAIN, structHash));
    }

    function _requireSigned(address signer, bytes32 digest, bytes calldata signature)
        internal
        view
    {
        require(SignatureChecker.isValidSignatureNow(signer, digest, signature), "bad signature");
    }

    function good_offer_checked_by_inherited_helper(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount
    ) external {
        _validateOffer(offer, signature);
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function good_offer_checked_two_calls_deep(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount
    ) external {
        _validateOfferVia(offer, signature);
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function good_offer_maker_copied_to_local(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount
    ) external {
        address maker = offer.maker;
        _validateOffer(offer, signature);
        token.safeTransferFrom(maker, address(this), amount);
    }

    function good_offer_signer_recovered_by_ecdsa(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount
    ) external {
        address signer = ECDSA.recover(_hash(offer), signature);
        if (signer != offer.maker) revert InvalidSignature();
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function good_checker_in_require(
        address from,
        address to,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount, nonce));
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_checker_result_in_local(
        address from,
        address to,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount, nonce));
        bool valid = SignatureChecker.isValidSignatureNow(from, digest, signature);
        if (!valid) revert InvalidSignature();
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_transfer_inside_checked_branch(
        address from,
        address to,
        uint256 amount,
        uint256 nonce,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount, nonce));
        if (SignatureChecker.isValidSignatureNow(from, digest, signature)) {
            IERC20(token).transferFrom(from, to, amount);
        }
    }

    function good_ecrecover(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        address signer = ecrecover(digest, v, r, s);
        require(signer == from, "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_erc1271_selector(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(
            IERC1271(from).isValidSignature(digest, signature) ==
                IERC1271.isValidSignature.selector,
            "bad signature"
        );
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_erc1271_magic_value(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(IERC1271(from).isValidSignature(digest, signature) == 0x1626ba7e, "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_typed_data_wrapper_over_bound_struct_hash(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = _typed(keccak256(abi.encode(TRANSFER_TYPEHASH, from, to, amount)));
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_digest_computed_by_caller_and_checked_in_callee(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = _typed(keccak256(abi.encode(TRANSFER_TYPEHASH, from, to, amount)));
        _requireSigned(from, digest, signature);
        IERC20(token).transferFrom(from, to, amount);
    }

    function good_digest_reads_signer_own_member(Order calldata order, bytes calldata signature)
        external
    {
        bytes32 digest = keccak256(abi.encode(order.maker, order.amount, order.id));
        require(SignatureChecker.isValidSignatureNow(order.maker, digest, signature), "bad signature");
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function good_typed_data_wrapper_over_whole_struct(
        Order calldata order,
        bytes calldata signature
    ) external {
        bytes32 digest = _typed(keccak256(abi.encode(order)));
        require(SignatureChecker.isValidSignatureNow(order.maker, digest, signature), "bad signature");
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_no_signature(address from, address to, uint256 amount) external {
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_signature_of_other_party(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount
    ) external {
        _validateTaker(offer, signature);
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function bad_checker_on_other_address(
        address from,
        address signer,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(SignatureChecker.isValidSignatureNow(signer, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_ecrecover_compared_to_other_address(
        address from,
        address to,
        uint256 amount,
        uint8 v,
        bytes32 r,
        bytes32 s
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(ecrecover(digest, v, r, s) == to, "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_validation_skipped_by_short_circuit(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount,
        bool trusted
    ) external {
        require(trusted || _isOfferValid(offer, signature), "invalid offer");
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function bad_checker_result_ignored(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        SignatureChecker.isValidSignatureNow(from, digest, signature);
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_checker_result_unused(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        bool valid = SignatureChecker.isValidSignatureNow(from, digest, signature);
        valid;
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_failed_check_does_not_revert(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        if (!SignatureChecker.isValidSignatureNow(from, digest, signature)) {
            failures++;
        }
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_transfer_follows_both_outcomes_of_check(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        if (SignatureChecker.isValidSignatureNow(from, digest, signature)) {
            failures++;
        }
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_signer_local_assigned_on_one_path(
        Offer calldata offer,
        bytes calldata signature,
        uint256 amount,
        bool useMaker
    ) external {
        address signer;
        if (useMaker) {
            signer = offer.maker;
        }
        require(SignatureChecker.isValidSignatureNow(signer, _hash(offer), signature), "bad signature");
        token.safeTransferFrom(offer.maker, address(this), amount);
    }

    function bad_signature_or_approval(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(
            SignatureChecker.isValidSignatureNow(from, digest, signature) || approved[from],
            "not authorized"
        );
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_check_only_on_one_path(
        address from,
        address to,
        uint256 amount,
        bool strict,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        if (strict) {
            require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        }
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_check_after_transfer(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        IERC20(token).transferFrom(from, to, amount);
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
    }

    function bad_from_replaced_after_check(
        address from,
        address replacement,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        from = replacement;
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_digest_chosen_by_caller(
        address from,
        address to,
        uint256 amount,
        bytes32 digest,
        bytes calldata signature
    ) external {
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_digest_of_caller_bytes(
        address from,
        address to,
        uint256 amount,
        bytes calldata payload,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(payload);
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_digest_of_caller_bytes_checked_in_callee(
        address from,
        address to,
        uint256 amount,
        bytes calldata payload,
        bytes calldata signature
    ) external {
        _requireSigned(from, keccak256(payload), signature);
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_digest_replaced_by_caller_bytes_on_one_path(
        address from,
        address to,
        uint256 amount,
        bytes calldata payload,
        bool replace,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        if (replace) {
            digest = keccak256(payload);
        }
        require(SignatureChecker.isValidSignatureNow(from, digest, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_digest_of_other_struct_member(Order calldata order, bytes calldata signature)
        external
    {
        bytes32 digest = keccak256(order.payload);
        require(SignatureChecker.isValidSignatureNow(order.maker, digest, signature), "bad signature");
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_digest_of_other_struct_parameter(
        Order calldata order,
        Order calldata other,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(other.maker, other.amount, other.id));
        require(SignatureChecker.isValidSignatureNow(order.maker, digest, signature), "bad signature");
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_digest_of_other_struct_member_checked_in_callee(
        Order calldata order,
        bytes calldata signature
    ) external {
        _requireSigned(order.maker, keccak256(order.payload), signature);
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_typed_data_wrapper_over_struct_hash(Order calldata order, bytes calldata signature)
        external
    {
        bytes32 digest = _typed(order.hash);
        require(SignatureChecker.isValidSignatureNow(order.maker, digest, signature), "bad signature");
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_digest_looked_up_by_struct_member(Order calldata order, bytes calldata signature)
        external
    {
        require(
            SignatureChecker.isValidSignatureNow(order.maker, digests[order.id], signature),
            "bad signature"
        );
        IERC20(token).transferFrom(order.maker, order.taker, order.amount);
    }

    function bad_typed_data_wrapper_over_caller_hash(
        address from,
        address to,
        uint256 amount,
        bytes32 orderHash,
        bytes calldata signature
    ) external {
        require(SignatureChecker.isValidSignatureNow(from, _typed(orderHash), signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_constant_digest(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        require(SignatureChecker.isValidSignatureNow(from, DOMAIN, signature), "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_erc1271_result_ignored(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        IERC1271(from).isValidSignature(digest, signature);
        IERC20(token).transferFrom(from, to, amount);
    }

    function bad_erc1271_compared_to_other_value(
        address from,
        address to,
        uint256 amount,
        bytes calldata signature
    ) external {
        bytes32 digest = keccak256(abi.encode(from, to, amount));
        require(IERC1271(from).isValidSignature(digest, signature) == 0x12345678, "bad signature");
        IERC20(token).transferFrom(from, to, amount);
    }
}
