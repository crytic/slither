import {A} from "./scope_a.sol";

contract B is A {
    constructor() {
        b();
    }
}