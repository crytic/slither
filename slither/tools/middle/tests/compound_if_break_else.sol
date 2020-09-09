pragma solidity >=0.4.16 <0.7.0;

contract Contract {
    uint public a;

    function f(uint input) public {
        while(input < 20) {
            if (input == 6) {
                break;
            } else {
                input -= 2;
            }
            input -= 1;
        }
    }
}