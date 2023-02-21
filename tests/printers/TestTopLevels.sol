// SPDX-License-Identifier: UNLICENSED
import {cry} from "./TopLevelImported.sol";
import "./TopLevelUsingFor.sol";

library Hello {
    function test() external pure returns(bool) {
        return true;
    }
}

function fill(uint num) returns(bytes32) {

    return cry(num);
}

function setNumber(uint256 newNumber) returns(bytes32) {
        bytes32 u = fill(newNumber);
        return keccak256(abi.encode(u));
        bool v = Hello.test();
    }

function attempt(uint x) returns(bytes32) {
    return setNumber(x);
}
contract TestTopLevelInherit is TopLevelUsingFor {
    function hi() public returns(bool v, bool u){
        v = canDoThing();
        bytes32 x = setNumber(7);
        u = getBit(Bitmap.wrap(9),8);
    }
}


contract TestTopLevels is TestTopLevelInherit{
    uint256 public number;
    function increment() public {
        number++;
        bytes32 v = attempt(7);
        x3();
        cry(7);
        canDoThing();

    }
    function x3() public returns(bytes32 k,bytes32 x){
        x = fill(5);
        bytes32 y = setNumber(4);
        k = attempt(7);
        increment();
        hi();
        bool tru = this.beExternal();
    }
    function beExternal() external returns(bool) {
        return Hello.test();
    }
}

