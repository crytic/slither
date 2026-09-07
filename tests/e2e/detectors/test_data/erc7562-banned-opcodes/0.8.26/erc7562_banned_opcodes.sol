// Stand-ins for the ERC-4337 v0.7 types, so the fixture compiles without imports 
struct PackedUserOperation {
    address sender;
    uint256 nonce;
    bytes initCode;
    bytes callData;
    bytes32 accountGasLimits;
    uint256 preVerificationGas;
    bytes32 gasFees;
    bytes paymasterAndData;
    bytes signature;
}

interface IAccount {
    function validateUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 missingAccountFunds
    ) external returns (uint256 validationData);
}

interface IPaymaster {
    function validatePaymasterUserOp(
        PackedUserOperation calldata userOp,
        bytes32 userOpHash,
        uint256 maxCost
    ) external returns (bytes memory context, uint256 validationData);

    function postOp(uint8 mode, bytes calldata context, uint256 actualGasCost, uint256 actualUserOpFeePerGas) external;
}

library Clock {
    function current() internal view returns (uint256) {
        return block.timestamp;
    }
}

// Abstract, so not deployable: the finding is attributeed to the concrete contract below.
abstract contract BasePaymaster is IPaymaster {
    event PostOp(uint256 at);

    function validatePaymasterUserOp(PackedUserOperation calldata userOp, bytes32, uint256 maxCost)
        external
        virtual
        override 
        returns (bytes memory context, uint256 validationData)
        {
            return _validate(userOp, maxCost);
        }

        function _validate(PackedUserOperation calldata userOp, uint256 maxCost)
            internal 
            virtual 
            returns (bytes memory context, uint256 validationData);

        // post Op runs in the execution phase, wheer the clock is allowed
        function postOp(uint8, bytes calldata, uint256, uint256) external virtual override {
            emit PostOp(block.timestamp);
        }
}

// BAD: TIMESTAMP is two internal calls away from the entry point
contract TimestampPaymaster is BasePaymaster {
    function _validate(PackedUserOperation calldata userOp, uint256 maxCost)
        internal 
        override 
        returns (bytes memory context, uint256 validationData)
        {
            context = abi.encode(userOp.sender, maxCost, block.timestamp);
            validationData = _pack(uint48(block.timestamp + 1 days), uint48(block.timestamp));
        }

        function _pack(uint48 validUntil, uint48 validAfter) internal pure returns (uint256) {
            return uint256(validUntil) << 160 | (uint256(validAfter) << 208); 
        }
}

// BAD: NUMBER is read inside a modifier 
contract ModifierPaymaster is IPaymaster {
    uint256 public deadline;

    modifier beforeDeadline() {
        require(block.number < deadline, "expired");
        _;
    }

    function validatePaymasterUserOp(PackedUserOperation calldata, bytes32, uint256)
        external 
        view 
        beforeDeadline
        returns (bytes memory context, uint256 validationData)
        {
            return ("", 0);
        }

        function postOp(uint8, bytes calldata, uint256, uint256) external override {}
}

// BAD: TIMESTAMP is read inside a library 
contract LibraryPaymaster is IPaymaster {
    function validatePaymasterUserOp(PackedUserOperation calldata, bytes32, uint256)
        external 
        view 
        returns (bytes memory context, uint256 validationData)
        {
            return (abi.encode(Clock.current()), 0);
        }

        function postOp(uint8, bytes calldata, uint256, uint256) external override {}
}

// BAD: the opcodes are spelled as inline assembly bulltins
contract AssemblyAccount is IAccount {
    function validateUserOp(PackedUserOperation calldata, bytes32, uint256)
        external 
        returns (uint256 validationData)
    {
        assembly {
            let t := timestamp()
            let o := origin()
            let b := selfbalance()
            validationData := or(or(t, o), b)
        }
    }
}

// Bad: every remaining banned opcode, spelled the Solidity way.
contract KitchenSinkAccount is IAccount {
    function validateUserOp(PackedUserOperation calldata userOp, bytes32, uint256 missingAccountFunds)
        external
        returns (uint256 validationData)
    {
        require(tx.origin == userOp.sender, "bundler");
        uint256 acc = tx.gasprice;
        acc += uint160(address(block.coinbase));
        acc += block.prevrandao;
        acc += block.gaslimit;
        acc += block.basefee;
        acc += block.number;
        acc += uint256(blockhash(1));
        acc += uint256(blobhash(0));
        acc += block.blobbasefee;
        if (missingAccountFunds > address(this).balance) {
            selfdestruct(payable(userOp.sender));
        }
        return acc;
    }
}

// Good: only permitted globals and opcodes are used during validation.
contract SafeAccount is IAccount {
    address public owner;
    address public entryPoint;

    function validateUserOp(PackedUserOperation calldata, bytes32 userOpHash, uint256 missingAccountFunds)
        external
        returns (uint256 validationData)
    {
        require(msg.sender == entryPoint, "entrypoint");
        uint256 chain = block.chainid;
        uint256 remaining = gasleft();
        address signer = ecrecover(userOpHash, 27, bytes32(chain), bytes32(remaining));
        if (missingAccountFunds > 0) {
            (bool ok, ) = msg.sender.call{value: missingAccountFunds}("");
            require(ok, "prefund");
        }
        return signer == owner ? 0 : 1;
    }

    // Reading the clock outside validation is fine.
    function execute() external view returns (uint256) {
        return block.timestamp;
    }
}

// Deployable base with an ORIGIN read. The non-overriding child must not duplicate the
// finding, and the child with a clean override must not inherit it.
contract OriginPaymaster is IPaymaster {
    mapping(address => bool) public allowedBundlers;

    function validatePaymasterUserOp(PackedUserOperation calldata, bytes32, uint256)
        external
        view
        virtual
        returns (bytes memory context, uint256 validationData)
    {
        require(allowedBundlers[tx.origin], "bundler");
        return ("", 0);
    }

    function postOp(uint8, bytes calldata, uint256, uint256) external override {}
}

contract OriginPaymasterChild is OriginPaymaster {}

contract OriginPaymasterFixed is OriginPaymaster {
    function validatePaymasterUserOp(PackedUserOperation calldata, bytes32, uint256)
        external
        view
        override
        returns (bytes memory context, uint256 validationData)
    {
        require(allowedBundlers[msg.sender], "bundler");
        return ("", 0);
    }
}

// Bad: the walk must terminate on a cycle and still reach the read at its end.
contract RecursiveAccount is IAccount {
    function validateUserOp(PackedUserOperation calldata, bytes32, uint256)
        external
        returns (uint256 validationData)
    {
        return _ping(3);
    }

    function _ping(uint256 n) internal returns (uint256) {
        if (n == 0) {
            return block.timestamp;
        }
        return _pong(n - 1);
    }

    function _pong(uint256 n) internal returns (uint256) {
        return _ping(n);
    }
}