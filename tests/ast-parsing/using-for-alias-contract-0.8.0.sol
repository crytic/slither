import "./using-for-alias-dep1.sol";

contract C {
    using {T3.a, T3.Lib.b} for uint256;

    function topLevel(uint256 value) public {
        value.a();
    }

    function libCall(uint256 value) public {
        value.b();
    }

}
