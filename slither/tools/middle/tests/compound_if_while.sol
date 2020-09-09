pragma solidity >=0.4.16 <0.7.0;

contract Contract {
    uint public a;

    function f(uint input) public {
        if (input < 8) {
            while (input > 0) {
                input--;
                a++;
            }
        } else {
            while (input < 20) {
                input++;
                a--;
            }
        }
    }
}