pragma solidity 0.8.7;

contract UnnamedTest {
    function unnamed0() external view returns(uint) {
        uint val = 1;
    } //returns: 0 (instead of 1)

    function unnamed1() external view returns(uint, uint val2) {
        uint val1 = 1;
        val2 = 2;
    } //returns: 0, 2 (instead of 1, 2)

    function unnamed2() external view returns(uint, uint) {
        uint val1 = 1;
        uint val2 = 2;
    } //returns: 0, 0 (instead of 1, 2)
}