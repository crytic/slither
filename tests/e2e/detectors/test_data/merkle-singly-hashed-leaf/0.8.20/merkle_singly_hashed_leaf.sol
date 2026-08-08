// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

// Minimal MerkleProof library interface for testing
library MerkleProof {
    function verify(
        bytes32[] memory proof,
        bytes32 root,
        bytes32 leaf
    ) internal pure returns (bool) {
        return processProof(proof, leaf) == root;
    }

    function verifyCalldata(
        bytes32[] calldata proof,
        bytes32 root,
        bytes32 leaf
    ) internal pure returns (bool) {
        return processProofCalldata(proof, leaf) == root;
    }

    function processProof(
        bytes32[] memory proof,
        bytes32 leaf
    ) internal pure returns (bytes32) {
        bytes32 computedHash = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            computedHash = _hashPair(computedHash, proof[i]);
        }
        return computedHash;
    }

    function processProofCalldata(
        bytes32[] calldata proof,
        bytes32 leaf
    ) internal pure returns (bytes32) {
        bytes32 computedHash = leaf;
        for (uint256 i = 0; i < proof.length; i++) {
            computedHash = _hashPair(computedHash, proof[i]);
        }
        return computedHash;
    }

    function _hashPair(bytes32 a, bytes32 b) private pure returns (bytes32) {
        return a < b ? keccak256(abi.encodePacked(a, b)) : keccak256(abi.encodePacked(b, a));
    }
}

contract MerkleAirdrop {
    bytes32 public merkleRoot;

    constructor(bytes32 _merkleRoot) {
        merkleRoot = _merkleRoot;
    }

    // BAD: No hashing at all - leaf is passed directly
    function claimNoHash(
        bytes32[] calldata proof,
        bytes32 leaf
    ) external {
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
    }

    // BAD: Only single hash
    function claimSingleHash(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 leaf = keccak256(abi.encodePacked(account, amount));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
    }

    // BAD: Single hash with verifyCalldata
    function claimSingleHashCalldata(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 leaf = keccak256(abi.encodePacked(account, amount));
        require(MerkleProof.verifyCalldata(proof, merkleRoot, leaf), "Invalid proof");
    }

    // BAD: Single hash with processProof
    function claimSingleHashProcess(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 leaf = keccak256(abi.encodePacked(account, amount));
        bytes32 computedRoot = MerkleProof.processProof(proof, leaf);
        require(computedRoot == merkleRoot, "Invalid proof");
    }

    // GOOD: Double hash (hash of hash)
    function claimDoubleHash(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encodePacked(account, amount))));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
    }

    // GOOD: Double hash with intermediate variable
    function claimDoubleHashIntermediate(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 innerHash = keccak256(abi.encodePacked(account, amount));
        bytes32 leaf = keccak256(abi.encodePacked(innerHash));
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
    }

    // GOOD: Double hash in helper function style
    function claimDoubleHashHelper(
        bytes32[] calldata proof,
        address account,
        uint256 amount
    ) external {
        bytes32 leaf = _hashLeaf(account, amount);
        require(MerkleProof.verify(proof, merkleRoot, leaf), "Invalid proof");
    }

    function _hashLeaf(address account, uint256 amount) internal pure returns (bytes32) {
        return keccak256(bytes.concat(keccak256(abi.encodePacked(account, amount))));
    }
}

// Test contract with different patterns
contract MerkleNFTAllowlist {
    bytes32 public merkleRoot;

    // BAD: Single hash
    function mintAllowlist(
        bytes32[] calldata proof,
        uint256 tokenId
    ) external {
        bytes32 leaf = keccak256(abi.encodePacked(msg.sender, tokenId));
        require(MerkleProof.verifyCalldata(proof, merkleRoot, leaf), "Not in allowlist");
    }

    // GOOD: Double hash
    function mintAllowlistSafe(
        bytes32[] calldata proof,
        uint256 tokenId
    ) external {
        bytes32 leaf = keccak256(bytes.concat(keccak256(abi.encodePacked(msg.sender, tokenId))));
        require(MerkleProof.verifyCalldata(proof, merkleRoot, leaf), "Not in allowlist");
    }
}
