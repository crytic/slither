pragma solidity >=0.4.16 <0.7.0;

contract Contract {
    uint public a;

    function f(uint input) public {
        for (uint i = 0; i < input;) {
            if (i == 0) {
                continue;
            }
            a = a + 1;
            i++;
        }
    }
}