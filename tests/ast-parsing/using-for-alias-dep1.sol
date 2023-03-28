import "./using-for-alias-dep2.sol" as T3;

function b(uint256 value) returns(bool) {
    return true;
}

library Lib {
    function a(uint256 value) public returns(bool) {
        return true;
    }
}
