// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

// Test case for issue #2073: function-summary printer incorrectly reports
// abi.encode, library calls, and struct field access as external calls

// Library for testing library calls
library SafeMath {
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        return a + b;
    }

    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        return a - b;
    }
}

// Interface for external calls
interface IExternalContract {
    function externalFunction() external returns (uint256);
    function anotherExternal(uint256 x) external returns (uint256);
}

// Contract to test Solidity built-in calls (should NOT be external calls)
contract TestBuiltins {
    function useAbiEncode(uint256 a, address b) external pure returns (bytes memory) {
        return abi.encode(a, b);
    }

    function useAbiEncodePacked(uint256 a) external pure returns (bytes memory) {
        return abi.encodePacked(a);
    }

    function useAbiEncodeWithSelector(bytes4 selector, uint256 a) external pure returns (bytes memory) {
        return abi.encodeWithSelector(selector, a);
    }

    function useAbiDecode(bytes memory data) external pure returns (uint256, address) {
        return abi.decode(data, (uint256, address));
    }

    function useKeccak256(bytes memory data) external pure returns (bytes32) {
        return keccak256(data);
    }
}

// Contract to test library calls (should NOT be external calls)
contract TestLibraryCalls {
    using SafeMath for uint256;

    function useLibraryWithUsing(uint256 a, uint256 b) external pure returns (uint256) {
        return a.add(b);
    }

    function useLibraryDirect(uint256 a, uint256 b) external pure returns (uint256) {
        return SafeMath.add(a, b);
    }

    function useMultipleLibraryCalls(uint256 a, uint256 b, uint256 c) external pure returns (uint256) {
        uint256 sum = SafeMath.add(a, b);
        return SafeMath.sub(sum, c);
    }
}

// Contract to test struct field access (should NOT be external calls)
contract TestStructAccess {
    struct Data {
        uint256 value;
        address owner;
    }

    Data private data;

    function setData(uint256 v, address o) external {
        data.value = v;
        data.owner = o;
    }

    function getValue() external view returns (uint256) {
        return data.value;
    }

    function getOwner() external view returns (address) {
        return data.owner;
    }
}

// Contract to test TRUE external calls (SHOULD be external calls)
contract TestExternalCalls {
    IExternalContract private externalContract;

    constructor(IExternalContract _external) {
        externalContract = _external;
    }

    function callExternal() external returns (uint256) {
        return externalContract.externalFunction();
    }

    function callExternalWithArg(uint256 x) external returns (uint256) {
        return externalContract.anotherExternal(x);
    }

    function callMultipleExternal(uint256 x) external returns (uint256) {
        uint256 a = externalContract.externalFunction();
        uint256 b = externalContract.anotherExternal(x);
        return a + b;
    }
}

// Mixed contract testing all patterns
contract TestMixed {
    using SafeMath for uint256;

    IExternalContract private externalContract;

    struct Config {
        uint256 threshold;
    }

    Config private config;

    constructor(IExternalContract _external) {
        externalContract = _external;
    }

    // Should have 1 external call (externalContract.externalFunction)
    // Should NOT count: abi.encode, SafeMath.add, config.threshold
    function mixedOperations(uint256 a, uint256 b) external returns (bytes memory) {
        uint256 sum = SafeMath.add(a, b);
        uint256 external_val = externalContract.externalFunction();
        uint256 threshold = config.threshold;
        return abi.encode(sum, external_val, threshold);
    }
}
