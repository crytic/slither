import {Z} from "./scope_z.sol";
contract A {
    function _a() private returns (Z) {

    }
    function b() public {
        _a();
    }
}