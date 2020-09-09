pragma solidity >=0.4.16 <0.7.0;

contract SimpleFor {
    uint public a;

    function SimpleWhileWithBreak(uint input) public {
        for (uint i = 0; i < input; i++) {
            a = a + 1;
            if (i == 8) {
                a = a * 2;
                break;
            }
        }
    }
}