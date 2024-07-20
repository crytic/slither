// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.0;

import {B} from "../sub2/B.sol";
import "./E.sol";

contract A is E {
    B public b;

    constructor(B b_contract) {
        b = b_contract;
    }
    function a() public view {
        b.b();
    }
}
