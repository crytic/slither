// SPDX-License-Identifier: UNLICENSED
import {TestTopLevels} from "./TestTopLevels.sol";
pragma solidity ^0.8.13;

function fill(uint num) returns(bytes memory) {
    return abi.encode(num);
}

function setNumber(uint256 newNumber) returns(bytes32) {
        bytes memory u = fill(newNumber);
        return keccak256(u);
    }

function cry(uint x) returns(bytes32) {
    return setNumber(x);
}


contract TopLevelImported {
    uint256 public number;
    TestTopLevels public test;
    function increment() public {
        number++;
        bytes32 u = setNumber(3);
        x2();
        bool v = test.beExternal();

    }
    function x2() public returns(bytes32 k){
        k = cry(7);
    }
    function a3() public returns(address) {
        increment();
        return ecrecover(cry(5), 2, bytes32(fill(5)), keccak256(abi.encode(5)));
    }
}