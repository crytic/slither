// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Unpacked {
    uint128 a;
    uint256 b;
    uint128 c;
}

contract Packed {
    uint128 a;
    uint128 c;
    uint256 b;
}

contract StructCases {
    struct UnpackedStruct { uint128 a; uint256 b; uint128 c; }
    struct PackedStruct { uint128 a; uint128 c; uint256 b; }
    struct DynamicStruct { uint128 a; string text; uint128 b; }
}

contract ExcludedConstants {
    uint128 a;
    uint256 constant SKIP = 3;
    uint128 c;
}

contract DynamicState {
    uint128 a;
    uint256[] values;
    uint128 c;
}

contract Parent { uint128 a; uint256 b; uint128 c; }
contract Child is Parent { uint128 d; }

contract AssemblyLayout {
    uint128 a;
    uint256 b;
    uint128 c;
    function load() external view returns (uint256 result) { assembly { result := sload(0) } }
}

contract Initializable {
    uint128 a;
    uint256 b;
    uint128 c;
    function initialize() external { a = 1; }
}

contract MixedWidths {
    uint160 a;
    uint160 b;
    uint96 c;
    uint96 d;
}

contract InitializerDependencies {
    uint128 a = 1;
    uint256 b = a;
    uint128 c = 2;
}
contract FixedState { uint128 a; uint256[2] b; uint128 c; }
type Small is uint128;
contract AliasTypes { Small a; uint256 b; Small c; }
