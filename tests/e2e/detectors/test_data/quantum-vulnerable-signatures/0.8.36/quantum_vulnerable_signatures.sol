// Minimal re-implementation of OpenZeppelin's ECDSA library, used to exercise
// the quantum-vulnerable-signatures detector against the `ECDSA.recover` pattern.
library ECDSA {
    function recover(bytes32 hash, bytes memory signature) internal pure returns (address) {
        require(signature.length == 65, "ECDSA: invalid signature length");
        bytes32 r;
        bytes32 s;
        uint8 v;
        assembly {
            r := mload(add(signature, 0x20))
            s := mload(add(signature, 0x40))
            v := byte(0, mload(add(signature, 0x60)))
        }
        return ecrecover(hash, v, r, s);
    }

    function tryRecover(
        bytes32 hash,
        bytes memory signature
    ) internal pure returns (address recoveredAddress, bool success) {
        recoveredAddress = recover(hash, signature);
        success = recoveredAddress != address(0);
    }
}

contract SignatureVerifier {
    using ECDSA for bytes32;

    address public lastSigner;

    function verifyBuiltin(bytes32 hash, uint8 v, bytes32 r, bytes32 s) external {
        lastSigner = ecrecover(hash, v, r, s);
    }

    function verifyLibrary(bytes32 hash, bytes memory sig) external {
        lastSigner = hash.recover(sig);
    }

    function verifyQualified(bytes32 hash, bytes memory sig) external {
        lastSigner = ECDSA.recover(hash, sig);
    }

    function claim(bytes32 claimHash, uint8 v, bytes32 r, bytes32 s) external pure returns (bool) {
        require(ecrecover(claimHash, v, r, s) != address(0), "invalid signature");
        return true;
    }
}

// Not flagged: the function name `recover` in a library with a different contract name.
library SigUtils {
    function recover(bytes32 hash, bytes memory signature) internal pure returns (bytes32) {
        return keccak256(abi.encodePacked(hash, signature));
    }
}

contract UsesSigUtils {
    using SigUtils for bytes32;

    function combine(bytes32 hash, bytes memory sig) external pure returns (bytes32) {
        return hash.recover(sig);
    }
}

// Not flagged: no signature verification at all.
contract NoSignatures {
    function hashIt(uint256 x) external pure returns (bytes32) {
        return keccak256(abi.encode(x));
    }
}
