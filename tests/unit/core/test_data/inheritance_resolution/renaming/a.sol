import {B as Base} from "./b.sol";
contract A is Base(address(0)) {
    constructor (address x) {}
}