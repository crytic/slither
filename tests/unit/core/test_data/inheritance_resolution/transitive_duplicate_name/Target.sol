pragma solidity ^0.8.0;

import {Lock} from "./BaseLock.sol";
import {IndirectBase} from "./IndirectBase.sol";

contract Target is IndirectBase, Lock {}
