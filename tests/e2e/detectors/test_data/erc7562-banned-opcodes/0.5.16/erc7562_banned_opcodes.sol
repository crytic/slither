// Bad: `now` and `block.difficulty` are the pre-0.7 spellings of TIMESTAMP and PREVRANDAO.
// The entry point is matched by name, so the argument list does not need to match ERC-4337.
contract LegacyAccount {
    function validateUserOp(bytes calldata, bytes32, uint256) external returns 
    (uint256) {
        require(now > 0, "clock");
        return block.difficulty;
    }
}

// NOT deployable: an unimplemented function makes a pre-0.6 contract abstrct
// without the keyword
contract ImplicitAbstractPaymaster {
    function validatePaymasterUserOp(bytes calldata, bytes32, uint256) external 
    returns (bytes memory, uint256) {
        return (abi.encode(_deadline()), 0);
    }

    function _deadline() internal returns (uint256);
}

// BAD: the concrete child inherits the entry point and supplies the read
contract ConcretePaymaster is ImplicitAbstractPaymaster {
    function _deadline() internal returns (uint256) {
        return now + 1 days;
    }
}