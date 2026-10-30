// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract CalldataCases {
    struct Pair { uint256 first; uint256 second; }
    struct Nested { uint256[] items; }
    modifier guard() { _; }

    function readArray(uint256[] memory data) external pure returns (uint256) { return data[0]; }
    function readBytes(bytes memory data) external pure returns (bytes32) { return keccak256(data); }
    function readStruct(Pair memory data) external pure returns (uint256) { return data.first; }
    function readString(string memory data) external pure returns (bytes32) { return keccak256(bytes(data)); }
    function readFixed(uint256[2] memory data) external pure returns (uint256) { return data[0]; }
    function readNested(Nested memory data) external pure returns (uint256) { return data.items[0]; }
    function alreadyCalldata(uint256[] calldata data) external pure returns (uint256) { return data[0]; }
    function mutate(uint256[] memory data) external pure returns (uint256) { data[0] = 3; return data[0]; }
    function mutateStruct(Pair memory data) external pure returns (uint256) { data.first = 3; return data.first; }
    function deleteElement(uint256[] memory data) external pure returns (uint256) { delete data[0]; return data[0]; }
    function reassigned(uint256[] memory data) external pure returns (uint256) { data = new uint256[](1); return data[0]; }
    function aliasMutation(uint256[] memory data) external pure returns (uint256) {
        uint256[] memory aliasData = data;
        aliasData[0] = 3;
        return data[0];
    }
    function castMutation(string memory data) external pure returns (bytes32) {
        bytes(data)[0] = 0x31;
        return keccak256(bytes(data));
    }
    function internalUse(uint256[] memory data) external pure returns (uint256) { return helper(data); }
    function returnAlias(uint256[] memory data) external pure returns (uint256[] memory result) {
        result = data;
        result[0] = 9;
    }
    function parameterAlias(uint256[] memory data, uint256[] memory aliasData) external pure returns (uint256) {
        aliasData = data;
        aliasData[0] = 9;
        return data[0];
    }
    function helper(uint256[] memory data) internal pure returns (uint256) { data[0] = 4; return data[0]; }
    function publicFunction(uint256[] memory data) public pure returns (uint256) { return data[0]; }
    function unused(uint256[] memory) external pure returns (uint256) { return 1; }
    function valueType(uint256 data) external pure returns (uint256) { return data; }
    function withModifier(uint256[] memory data) external pure guard returns (uint256) { return data[0]; }
    function withAssembly(bytes memory data) external pure returns (uint256 size) { assembly { size := mload(data) } }
}
