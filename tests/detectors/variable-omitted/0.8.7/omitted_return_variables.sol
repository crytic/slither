pragma solidity 0.8.7;

contract OmittedTest {
    function omitted0() external view returns(uint val) {
        val = 1;
        return 0;
    } //returns: 0 (instead of 1)

    function omitted1() external view returns(uint val1) {
        val1 = 1;
        uint val2 = 0;
        return val2;
    } //returns: 0 (instead of 1)

    function omitted2() external view returns(uint val1, uint val2) {
        val1 = 1;
        val2 = 2;
        uint val3 = 3;
        return (val3, 4);
    }//returns: (3, 4) (instead of 1, 2)
}