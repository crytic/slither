pragma solidity >=0.4.24;

contract SafeAdd {
    function add(uint x, uint y) public pure returns (uint z) {
        require((z = x + y) >= x);
    }
    function add_v2(uint x, uint y) public pure returns (uint z) {
        require((z = x + y) >= x);
    }
}
