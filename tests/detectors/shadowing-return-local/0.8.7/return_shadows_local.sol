pragma solidity 0.8.7;

contract ShadowedTest {
    function shadowed0() external view returns(uint val) {
        uint val = 1;
    } //returns: 0 (instead of 1)

    function shadowed1() external view returns(uint val1, uint val2) {
        uint val1 = 1;
        val2 = 2;
    } //returns: 0, 2 (instead of 1, 2)

    function shadowed2() external view returns(uint val1, uint val2) {
        uint val1 = 1;
        uint val2 = 2;
    } //returns: 0, 0 (instead of 1, 2)
}