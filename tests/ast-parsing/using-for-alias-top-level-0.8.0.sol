import "./using-for-alias-dep1.sol";

using {T3.a, T3.Lib.b} for uint256;

contract C {

    function topLevel(uint256 value) public {
        value.a();
    }

    function libCall(uint256 value) public {
        value.b();
    }

}
