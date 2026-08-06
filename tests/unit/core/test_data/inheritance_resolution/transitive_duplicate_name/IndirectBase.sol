pragma solidity ^0.8.0;

import {Lock} from "./LockLibrary.sol";

abstract contract IndirectBase {
    using Lock for uint256;
}
